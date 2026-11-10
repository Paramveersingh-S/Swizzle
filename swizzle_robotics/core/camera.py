from __future__ import annotations
import time
import numpy as np
from typing import Optional, Tuple

class MockCamera:
    """
    Synthetic camera generator simulating a 224x224 tabletop robotic arm
    and pick-and-place cube. Ideal for testing and headless CI.
    """

    def __init__(self, fps: float = 30.0, width: int = 224, height: int = 224):
        self.fps = fps
        self.width = width
        self.height = height
        self.frame_idx = 0
        self.interval = 1.0 / fps
        self._last_time = time.perf_counter()

    def read(self) -> Tuple[bool, np.ndarray]:
        elapsed = time.perf_counter() - self._last_time
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last_time = time.perf_counter()

        self.frame_idx += 1
        # Create tabletop background: grayish wood surface
        frame = np.full((self.height, self.width, 3), fill_value=180, dtype=np.uint8)

        # Add static background grid
        frame[::32, :, :] = 160
        frame[:, ::32, :] = 160

        # Moving cube trajectory (pick-and-place)
        t = self.frame_idx * 0.05
        cx = int(self.width / 2 + 50 * np.sin(t))
        cy = int(self.height / 2 + 30 * np.cos(t))

        # Draw red cube (24x24 pixels)
        r = 12
        y1, y2 = max(0, cy - r), min(self.height, cy + r)
        x1, x2 = max(0, cx - r), min(self.width, cx + r)
        frame[y1:y2, x1:x2, :] = [40, 40, 220]  # Red in BGR

        return True, frame

    def release(self):
        pass

class LiveCamera:
    """
    Production OpenCV Camera Ingestion.
    Automatically grabs, crops, and resizes frames to (224, 224).
    Falls back gracefully to MockCamera if physical webcam is inaccessible.
    """

    def __init__(self, camera_id: int = 0, target_size: int = 224, fps: float = 30.0):
        self.camera_id = camera_id
        self.target_size = target_size
        self.fps = fps
        self._cap = None
        self._is_mock = False

        try:
            import cv2
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FPS, fps)
                ret, frame = cap.read()
                if ret and frame is not None:
                    self._cap = cap
                else:
                    cap.release()
                    self._cap = MockCamera(fps=fps, width=target_size, height=target_size)
                    self._is_mock = True
            else:
                self._cap = MockCamera(fps=fps, width=target_size, height=target_size)
                self._is_mock = True
        except Exception:
            self._cap = MockCamera(fps=fps, width=target_size, height=target_size)
            self._is_mock = True

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def read(self) -> Tuple[bool, np.ndarray]:
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return False, np.zeros((self.target_size, self.target_size, 3), dtype=np.uint8)

        # Center-crop to square then resize
        h, w = frame.shape[:2]
        min_dim = min(h, w)
        cy, cx = h // 2, w // 2
        cropped = frame[cy - min_dim // 2 : cy + min_dim // 2, cx - min_dim // 2 : cx + min_dim // 2]

        try:
            import cv2
            resized = cv2.resize(cropped, (self.target_size, self.target_size), interpolation=cv2.INTER_AREA)
            return True, resized
        except Exception:
            return True, cropped[: self.target_size, : self.target_size]

    def release(self):
        if self._cap:
            self._cap.release()
