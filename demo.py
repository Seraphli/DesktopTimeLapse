from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import BooleanProperty

import mss
import mss.tools
import cv2
import numpy as np

video_name = 'Output.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')


def numpy_flip(im):
    """ Most efficient Numpy version as of now. """
    frame = np.array(im, dtype=np.uint8)
    frame = np.flip(frame[:, :, :3], 2)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame


class MyApp(App):
    state = BooleanProperty(False)

    def build(self):
        self.sct = mss.mss()
        self.video = None
        self.title = 'Desktop Time Lapse'
        layout = BoxLayout(orientation='vertical')
        self.label = Label(text='State: False')
        self.btn = Button(text='Start')
        layout.add_widget(self.label)
        layout.add_widget(self.btn)
        self.btn.bind(on_press=self.click_btn)
        self.event = Clock.schedule_interval(self.record_image, 0.2)
        return layout

    def click_btn(self, instance):
        self.state = not self.state
        self.label.text = 'State: {}'.format(self.state)
        if self.btn.text == 'Start':
            self.btn.text = 'Stop'
        else:
            self.btn.text = 'Start'

    def save_video(self):
        if self.video is not None:
            self.video.release()
            self.video = None

    def on_stop(self):
        self.save_video()

    def on_state(self, instance, value):
        self.save_video()

    def record_image(self, dt):
        if not self.state:
            return
        sct_img = self.sct.grab(self.sct.monitors[1])
        if self.video is None:
            self.video = cv2.VideoWriter(
                video_name, fourcc, 30, (sct_img.width, sct_img.height))
        self.video.write(numpy_flip(sct_img))


if __name__ == '__main__':
    MyApp().run()
