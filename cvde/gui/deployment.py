
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


class Deployment:
    device = 'cpu'
    # device = 'cuda'

    def __init__(self) -> None:

        self.pipeline = Deployment.get_rs_stream()

        if st.checkbox('Use gpu'):
            self.device = 'cuda'

        im_size = 512

        self.resize = A.Compose([
            A.LongestMaxSize(max_size=im_size,
                             interpolation=cv2.INTER_NEAREST, p=1.0),
            A.PadIfNeeded(min_height=im_size, min_width=im_size,
                          p=1.0, border_mode=cv2.BORDER_ISOLATED)])

        self.model = smp.DeepLabV3Plus(
            encoder_name='resnet34', in_channels=3, classes=6).to(self.device)

        self.runs = os.listdir('log')
        t = JobTracker.from_log(self.runs[0])

        weights = os.listdir(t.weights_root)
        selected_weigts = st.selectbox('weights', weights)
        weight_path = os.path.join(t.weights_root, selected_weigts)
        self.model.load_state_dict(torch.load(weight_path))

        mean = [0.485, 0.456, 0.406]  # image net
        std = [0.229, 0.224, 0.225]  # image net
        self.normalize = torchvision.transforms.Normalize(mean, std)

    @st.cache_resource
    @staticmethod
    def get_rs_stream():
        pipeline = rs.pipeline()

        # Configure streams
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

        pipeline.start(config)
        return pipeline

    def run(self):
        live_preview = st.checkbox('live preview')
        alpha = st.slider('Overlay', min_value=0,
                          max_value=100, value=50) / 100.

        img_preview = st.empty()

        while True:

            frames = self.pipeline.wait_for_frames()

            color_frame = frames.get_color_frame()

            img = np.asanyarray(color_frame.get_data())
            img = self.resize(image=img)['image']

            input = self.normalize(
                torchvision.transforms.ToTensor()(img)).to(self.device)  # [3, H, W]
            input = torch.unsqueeze(input, 0)

            pred = self.model.predict(input)
            pred = torch.argmax(pred, 1).squeeze()
            colored_pred = Blender.color_seg(pred.cpu().numpy())

            overlay = cv2.addWeighted(img, 1 - alpha, colored_pred, alpha, 0.0)

            with img_preview:
                st.image(overlay)

            if not live_preview:
                break
