import time
import numpy as np
import streamlit as st
import pyrealsense2 as rs
import cv2
import torch
import torchvision
import segmentation_models_pytorch as smp
import albumentations as A
import os

from test_workspace.datasets.blender import Blender
from cvde.workspace import Workspace as WS
from cvde.job_tracker import JobTracker
from test_workspace.models.deeplab import get_model


class Deployment:
    device = 'cpu'
    # device = 'cuda'

    def __init__(self) -> None:

        self.pipeline = Deployment.get_rs_stream()

        if st.checkbox('Use gpu', key='depl_use_gpu'):
            self.device = 'cuda'

        st.checkbox('live preview', key='depl_live_preview')

        self.runs = os.listdir('log')
        self.runs.sort(reverse=True)
        selected_run = st.selectbox(
            'Trained model from', self.runs, key='depl_selected_run')
        t = JobTracker.from_log(selected_run)
        weights = os.listdir(t.weights_root)
        weights.sort()
        selected_weigts = st.select_slider(
            'weights', weights, value=weights[-1])
        weights_path = os.path.join(t.weights_root, selected_weigts)

        self.model = get_model(weights_path=weights_path, **
                               t.config['model'], **t.config['shared']).to(self.device)

        # this part is not generic yet
        im_size = {**t.config['train_config'], **t.config['shared']}['im_size']
        self.resize = A.Compose([
            A.LongestMaxSize(max_size=im_size,
                             interpolation=cv2.INTER_NEAREST, p=1.0),
            A.PadIfNeeded(min_height=im_size, min_width=im_size,
                          p=1.0, border_mode=cv2.BORDER_ISOLATED)])
        mean = [0.485, 0.456, 0.406]  # image net
        std = [0.229, 0.224, 0.225]  # image net
        self.normalize = torchvision.transforms.Normalize(mean, std)

    @st.cache_resource
    @staticmethod
    def get_rs_stream():
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)
        pipeline.start(config)
        return pipeline

    def run(self):
        alpha = st.slider('Overlay', min_value=0,
                          max_value=100, value=50) / 100.

        selected_class = st.select_slider('Class', Blender.cls_dict.keys())

        fps_cont = st.empty()
        c1, c2 = st.columns(2)
        img_preview = c1.empty()
        confidence_preview = c2.empty()
        t_last = time.perf_counter()

        last_dt = None
        while True:
            dt = time.perf_counter() - t_last
            t_last = time.perf_counter()
            if last_dt is not None:
                fps_cont.metric('FPS', value=f"{2 / (dt+last_dt):.1f}")
            last_dt = dt

            frames = self.pipeline.wait_for_frames()

            color_frame = frames.get_color_frame()

            img = np.asanyarray(color_frame.get_data())
            img = self.resize(image=img)['image']

            input = self.normalize(
                torchvision.transforms.ToTensor()(img)).to(self.device)  # [3, H, W]
            input = torch.unsqueeze(input, 0)

            pred = self.model.predict(input)

            id = Blender.cls_dict[selected_class]
            confidence = torch.sigmoid(pred[0, id]).cpu().numpy()

            pred = torch.argmax(pred, 1).squeeze()
            colored_pred = Blender.color_seg(pred.cpu().numpy())

            confidence = (confidence * 255).astype(np.uint8)
            confidence = cv2.applyColorMap(confidence, cv2.COLORMAP_INFERNO)

            overlay = cv2.addWeighted(img, 1 - alpha, colored_pred, alpha, 0.0)

            img_preview.image(overlay)
            confidence_preview.image(
                confidence, caption=f"Confidence for {selected_class}")

            if not st.session_state['depl_live_preview']:
                break
