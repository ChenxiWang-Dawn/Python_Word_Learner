#!/usr/bin/env python3

import os
import sys
import threading
import time
import pygame
from enum import Enum
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer


class PlayerState(Enum):
    IDLE = 0
    PLAYING = 1
    PAUSED = 2


class TtsPlayer:
    def __init__(self):
        self.state = PlayerState.IDLE
        self.lock = threading.Lock()
        self.temp_file = 'temp_audio.mp3'
        pygame.mixer.init()
        self._init_dashscope_api_key()

    def _init_dashscope_api_key(self):
        '''
        Set DashScope API-key from environment variable or default value
        '''
        if 'DASHSCOPE_API_KEY' in os.environ:
            dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
        else:
            dashscope.api_key = '<your-dashscope-api-key>'  # set API-key manually

    def play(self, text):
        with self.lock:
            if self.state != PlayerState.IDLE:
                raise Exception("Cannot play while audio is already playing or paused")
            
            self.state = PlayerState.PLAYING
        
        try:
            # Synthesize speech

            speech_synthesizer = SpeechSynthesizer(model='cosyvoice-v1',
                                                   voice='loongstella',
                                                   callback=None)
            audio = speech_synthesizer.call(text)
            if audio is None:
                print("Error: Failed to synthesize speech - audio is None")
                with self.lock:
                    self.state = PlayerState.IDLE
                return
            
            # Save to temporary file
            with open(self.temp_file, 'wb') as f:
                f.write(audio)
            
            # Play the audio
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy() and self.state == PlayerState.PLAYING:
                time.sleep(0.1)
            
            # If we exited the loop and state is still PLAYING, it means playback finished naturally
            with self.lock:
                if self.state == PlayerState.PLAYING:
                    self.state = PlayerState.IDLE
            
            print(f'Played text: {text}')
            print('[Metric] requestId: {}, first package delay ms: {}'.format(
                speech_synthesizer.get_last_request_id(),
                speech_synthesizer.get_first_package_delay()))
                
        except Exception as e:
            print(f"Error during speech synthesis or playback: {str(e)}")
            with self.lock:
                self.state = PlayerState.IDLE

    def pause(self):
        with self.lock:
            if self.state == PlayerState.PLAYING:
                pygame.mixer.music.pause()
                self.state = PlayerState.PAUSED
                print("Playback paused")
            else:
                print("Cannot pause: No audio is playing")

    def resume(self):
        with self.lock:
            if self.state == PlayerState.PAUSED:
                pygame.mixer.music.unpause()
                self.state = PlayerState.PLAYING
                print("Playback resumed")
            else:
                print("Cannot resume: Audio is not paused")

    def stop(self):
        with self.lock:
            if self.state != PlayerState.IDLE:
                pygame.mixer.music.stop()
                self.state = PlayerState.IDLE
                print("Playback stopped")
            else:
                print("Cannot stop: No audio is playing or paused")


# Test case
if __name__ == '__main__':
    player = TtsPlayer()
    
    def test_play_conflict():
        print("\nTest 1: Play conflict (multithreaded)")
        # First thread plays normally
        def first_thread_play():
            player.play("这是第一个线程的播放测试 This is a playback test for the first thread")
        
        # 创建并启动第一个播放线程
        first_thread = threading.Thread(target=first_thread_play)
        first_thread.start()
        time.sleep(0.2)  # Give a moment for playback to start
        # Second thread tries to play while first is playing (should raise exception)
        try:
            player.play("这个不应该播放，因为第一个线程还在播放 This should not play because the first thread is still playing")
            print("Test failed: Should have raised an exception")
        except Exception as e:
            print(f"Test passed: {str(e)}")
        first_thread.join()
        
    
    def test_pause_resume_stop():
        print("\nTest 2: Pause, resume, stop (multithreaded)")
        
        # Start playback in a separate thread
        def play_thread():
            try:
                player.play("这是暂停、恢复和停止的测试 This is a test for pause, resume, and stop")
                print("Play thread completed normally")
            except Exception as e:
                print(f"Play thread exception: {str(e)}")
        
        # 创建并启动播放线程
        play_t = threading.Thread(target=play_thread)
        play_t.start()
        
        time.sleep(3)
        
        # 主线程暂停播放
        player.pause()
        print("Paused playback")
        
        # 2秒后恢复播放
        time.sleep(2)
        player.resume()
        print("Resumed playback")
        
        # 3秒后停止播放
        time.sleep(3)
        player.stop()
        print("Stopped playback")
        
        # 等待播放线程结束
        play_t.join()
    
    # Run the tests sequentially
    test_play_conflict()
    test_pause_resume_stop()
    
    print("\nAll tests completed")
