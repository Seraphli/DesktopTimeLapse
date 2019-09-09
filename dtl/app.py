from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.config import Config

from vidgear.gears import ScreenGear
from vidgear.gears import WriteGear
from dtl.constants import *
from dtl.util import get_path

from threading import Thread, Event
import datetime
import json
import re


class FloatInput(TextInput):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


class TimerThread(Thread):
    def __init__(self, interval, function):
        super(TimerThread, self).__init__()
        self.daemon = True
        self.interval = interval
        self.stopped = Event()
        self.function = function

    def run(self):
        while not self.stopped.wait(self.interval):
            Thread(target=self.function).start()


class DTLApp(App):
    state = False
    interval = 1.0
    stream = None
    writer = None
    timer = None

    def load_custom_config(self):
        path = get_path('config', parent=True) + '/cfg.json'
        try:
            config = json.load(open(path))
        except:
            config = DEFAULT_CONFIG
        json.dump(config, open(path, 'w'))
        return config

    def build(self):
        self.custom_cfg = self.load_custom_config()
        self.interval = self.custom_cfg['interval']
        self.title = 'Desktop Time Lapse'
        layout = BoxLayout(orientation='vertical')
        h_layout_1 = BoxLayout(orientation='horizontal')
        h_layout_1.add_widget(Label(text='Interval:', size_hint=(0.25, 1)))
        self.text_input = FloatInput(
            text=str(self.interval), size_hint=(0.25, 1), multiline=False)
        h_layout_1.add_widget(self.text_input)
        set_btn = Button(text='Set', size_hint=(0.5, 1))
        set_btn.bind(on_press=self.set_btn_press)
        h_layout_1.add_widget(set_btn)
        layout.add_widget(h_layout_1)

        h_layout_2 = BoxLayout(orientation='horizontal')
        h_layout_2.add_widget(Label(text='State:'))
        self.state_label = Label(text='Idle')
        h_layout_2.add_widget(self.state_label)
        layout.add_widget(h_layout_2)

        h_layout_3 = BoxLayout(orientation='horizontal')
        h_layout_3.add_widget(Label(text='Duration:'))
        self.rt_label = Label(text='0')
        h_layout_3.add_widget(self.rt_label)
        h_layout_3.add_widget(Label(text='VTime:'))
        self.vt_label = Label(text='0')
        h_layout_3.add_widget(self.vt_label)
        layout.add_widget(h_layout_3)

        h_layout_4 = BoxLayout(orientation='horizontal')
        h_layout_4.add_widget(Label(text='Frames:', size_hint=(0.25, 1)))
        self.frame_label = Label(text='0', size_hint=(0.25, 1))
        h_layout_4.add_widget(self.frame_label)
        self.record_btn = Button(text='Start Record', size_hint=(0.5, 1))
        h_layout_4.add_widget(self.record_btn)
        layout.add_widget(h_layout_4)
        self.record_btn.bind(on_press=self.record_btn_press)

        self.event = Clock.schedule_interval(self.update_label, 0.1)
        return layout

    def set_btn_press(self, instance):
        try:
            interval = float(self.text_input.text)
            if int(interval / 0.01) > 0:
                self.interval = 0.01 * int(interval / 0.01)
            self.text_input.text = str(self.interval)
        except:
            pass

    def record_btn_press(self, instance):
        if not self.state:
            self.state_label.text = 'Record'
            self.record_btn.text = 'Stop Record'
            self.start_time = datetime.datetime.now()
            self.stream = ScreenGear(
                monitor=1, **{'THREADED_QUEUE_MODE': False}).start()
            output_params = {'-vcodec': 'libx264', '-crf': 0,
                             '-preset': 'fast'}
            self.video_path = get_path('video', parent=True) + '/' + \
                              self.start_time.strftime("%Y-%m-%d %H_%M_%S.mp4")
            self.writer = WriteGear(
                output_filename=self.video_path,
                compression_mode=True, **output_params)
            self.count = 0
            self.count_frames = 0
            self.timer = TimerThread(self.interval, self.record_image)
            self.timer.start()
        else:
            self.timer.stopped.set()
            self.state_label.text = 'Idle'
            self.record_btn.text = 'Start Record'
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

    def record_image(self):
        if not self.state:
            return
        frame = self.stream.read()
        self.writer.write(frame)
        self.count_frames += 1

    def update_label(self, dt):
        if not self.state:
            return
        self.frame_label.text = str(self.count_frames)
        d_time = str(datetime.datetime.now() - self.start_time)
        self.rt_label.text = d_time[:d_time.find('.')]
        v_time = str(datetime.timedelta(seconds=int(self.count_frames // 25)))
        self.vt_label.text = v_time


def run_app():
    Config.set('graphics', 'width', str(WIDTH))
    Config.set('graphics', 'height', str(HEIGHT))
    Config.set('graphics', 'resizable', '0')
    Config.write()
    DTLApp().run()


if __name__ == '__main__':
    run_app()
