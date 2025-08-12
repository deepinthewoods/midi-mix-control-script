# uncompyle6 version 3.9.1
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.12.2 (main, Feb  6 2024, 20:19:44) [Clang 15.0.0 (clang-1500.1.0.2.5)]
# Embedded file name: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/MIDI_Mix/MixerComponent.py
# Compiled at: 2024-03-09 01:30:22
# Size of source mod 2**32: 1306 bytes
from __future__ import absolute_import, print_function, unicode_literals
from _Framework.Control import ButtonControl
from _APC.MixerComponent import MixerComponent as MixerComponentBase

class MixerComponent(MixerComponentBase):
    bank_up_button = ButtonControl(color="DefaultButton.Off",
      pressed_color="DefaultButton.On")
    bank_down_button = ButtonControl(color="DefaultButton.Off",
      pressed_color="DefaultButton.On")

    def __init__(self, parent_surface=None, *a, **k):
        super(MixerComponent, self).__init__(*a, **k)
        self._parent_surface = parent_surface
        self._current_cc_bank = 0  # Track which CC bank we're on (0, 1, 2)
        self._max_cc_banks = 3
        self._bank_left_pressed = False
        self._bank_right_pressed = False

    def set_send_controls(self, controls):
        self._send_controls = controls
        if controls:
            for index, strip in enumerate(self._channel_strips):
                strip.set_send_controls((
                 controls.get_button(index, 0), controls.get_button(index, 1)))

    @bank_up_button.pressed
    def bank_up_button(self, button):
        self._bank_right_pressed = True
        if self._bank_left_pressed:
            # Both buttons pressed - set to page 3 (CC bank 2) and track bank 3 (tracks 17-24)
            self._set_cc_bank_direct(2)
            self.set_track_offset(16)  # Tracks 17-24 (0-indexed = 16)
        else:
            # Only right button - set to page 2 (CC bank 1) and track bank 2 (tracks 9-16)
            self._set_cc_bank_direct(1)
            self.set_track_offset(8)   # Tracks 9-16 (0-indexed = 8)
    
    @bank_up_button.released
    def bank_up_button_released(self, button):
        self._bank_right_pressed = False

    @bank_down_button.pressed
    def bank_down_button(self, button):
        self._bank_left_pressed = True
        if self._bank_right_pressed:
            # Both buttons pressed - set to page 3 (CC bank 2) and track bank 3 (tracks 17-24)
            self._set_cc_bank_direct(2)
            self.set_track_offset(16)  # Tracks 17-24 (0-indexed = 16)
        else:
            # Only left button - set to page 1 (CC bank 0) and track bank 1 (tracks 1-8)
            self._set_cc_bank_direct(0)
            self.set_track_offset(0)   # Tracks 1-8 (0-indexed = 0)
    
    @bank_down_button.released
    def bank_down_button_released(self, button):
        self._bank_left_pressed = False

    def _set_cc_bank_direct(self, bank):
        """Directly set CC bank (0=page1, 1=page2, 2=page3)"""
        if 0 <= bank < self._max_cc_banks and bank != self._current_cc_bank:
            old_bank = self._current_cc_bank
            self._current_cc_bank = bank
            if self._parent_surface:
                self._parent_surface._update_encoders_for_cc_bank(self._current_cc_bank)
                self._update_bank_button_leds()

    def _cycle_cc_bank(self, direction):
        """Cycle through CC banks (0, 1, 2) - keeping for compatibility"""
        old_bank = self._current_cc_bank
        self._current_cc_bank = (self._current_cc_bank + direction) % self._max_cc_banks
        
        if old_bank != self._current_cc_bank and self._parent_surface:
            self._parent_surface._update_encoders_for_cc_bank(self._current_cc_bank)
            self._update_bank_button_leds()

    def get_current_cc_bank(self):
        """Get current CC bank number"""
        return self._current_cc_bank

    def set_cc_bank(self, bank):
        """Manually set CC bank"""
        self._set_cc_bank_direct(bank)

    def _update_bank_button_leds(self):
        """Update bank button LEDs based on current CC bank"""
        if not hasattr(self, 'bank_up_button') or not hasattr(self, 'bank_down_button'):
            return
            
        # Page 1 (Bank 0): Bank Left LED on, Bank Right LED off
        # Page 2 (Bank 1): Bank Left LED off, Bank Right LED on  
        # Page 3 (Bank 2): Both LEDs on
        
        if self._current_cc_bank == 0:  # Page 1
            self.bank_down_button.color = "DefaultButton.On"
            self.bank_up_button.color = "DefaultButton.Off"
        elif self._current_cc_bank == 1:  # Page 2
            self.bank_down_button.color = "DefaultButton.Off"
            self.bank_up_button.color = "DefaultButton.On"
        elif self._current_cc_bank == 2:  # Page 3
            self.bank_down_button.color = "DefaultButton.On"
            self.bank_up_button.color = "DefaultButton.On"

    def set_enabled(self, enable):
        """Override to update LEDs when component is enabled"""
        super(MixerComponent, self).set_enabled(enable)
        if enable:
            self._update_bank_button_leds()