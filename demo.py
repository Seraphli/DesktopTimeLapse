import os

os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.config import Config

from vidgear.gears import ScreenGear
from vidgear.gears import WriteGear

import datetime

VIDEO_NAME = 'Output.mp4'

output_params = {"-vcodec": "libx264", "-crf": 0,
                 "-preset": "fast"}


class MyApp(App):
    state = BooleanProperty(False)

    def build(self):
        self.interval = 5
        self.stream = None
        self.writer = None

        self.title = 'Desktop Time Lapse'
        layout = BoxLayout(orientation='vertical')

        h_layout = BoxLayout(orientation='horizontal')
        h_layout.add_widget(Label(text='State:'))
        self.state_label = Label(text='Idle')
        h_layout.add_widget(self.state_label)
        h_layout.add_widget(Label(text='Duration:'))
        self.rt_label = Label(text='0')
        h_layout.add_widget(self.rt_label)
        layout.add_widget(h_layout)

        h_layout = BoxLayout(orientation='horizontal')
        _h_layout = BoxLayout(orientation='horizontal')
        _h_layout.add_widget(Label(text='VTime:'))
        self.vt_label = Label(text='0')
        _h_layout.add_widget(self.vt_label)
        h_layout.add_widget(_h_layout)
        self.btn = Button(text='Start Record')
        h_layout.add_widget(self.btn)
        layout.add_widget(h_layout)
        self.btn.bind(on_press=self.click_btn)
        self.event = Clock.schedule_interval(self.record_image, 0.1)
        return layout

    def click_btn(self, instance):
        if not self.state:
            self.state_label.text = 'Record'
            self.btn.text = 'Stop Record'
            self.start_time = datetime.datetime.now()
            self.stream = ScreenGear(
                monitor=1, **{'THREADED_QUEUE_MODE': False}).start()
            self.writer = WriteGear(output_filename=VIDEO_NAME,
                                    compression_mode=True,
                                    **output_params)
            self.count = 0
            self.count_frames = 0
        else:
            self.state_label.text = 'Idle'
            self.btn.text = 'Start Record'
            self.stream.stop()
            self.stream = None
            self.writer.close()
            self.writer = None
            self.start_time = None
        self.state = not self.state

    def on_stop(self):
        if self.writer:
            self.writer.close()
        if self.stream:
            self.stream.stop()

    def record_image(self, dt):
        if not self.state:
            return
        if self.count % int(self.interval / 0.1) == 0:
            frame = self.stream.read()
            self.writer.write(frame)
            self.count_frames += 1
        self.count += 1
        d_time = str(datetime.datetime.now() - self.start_time)
        self.rt_label.text = d_time[:d_time.find('.')]
        v_time = str(datetime.timedelta(seconds=int(self.count_frames // 25)))
        self.vt_label.text = v_time


if __name__ == '__main__':
    Config.set('graphics', 'width', '400')
    Config.set('graphics', 'height', '100')
    Config.set('graphics', 'resizable', '0')
    Config.write()
    MyApp().run()
