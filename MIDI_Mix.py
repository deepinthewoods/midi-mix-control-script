# uncompyle6 version 3.9.1
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.12.2 (main, Feb  6 2024, 20:19:44) [Clang 15.0.0 (clang-1500.1.0.2.5)]
# Embedded file name: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/MIDI_Mix/MIDI_Mix.py
# Compiled at: 2024-03-09 01:30:22
# Size of source mod 2**32: 3705 bytes
from __future__ import absolute_import, print_function, unicode_literals
from builtins import object, range
from itertools import chain
from _Framework.ButtonElement import Color
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ControlSurface import OptimizedControlSurface
from _Framework.Dependency import inject
from _Framework.Layer import Layer
from _Framework.Skin import Skin
from _Framework.Util import const
from .ControlElementUtils import make_button, make_button_row, make_encoder, make_slider
from .MixerComponent import MixerComponent

NUM_TRACKS = 8

# CC Bank 0 (Page 1) - Original SEND_IDS
SEND_IDS_BANK0 = ((16, 20, 24, 28, 46, 50, 54, 58), (17, 21, 25, 29, 47, 51, 55, 59))
PAN_IDS_BANK0 = list(chain(range(18, 31, 4), range(48, 61, 4)))

# CC Bank 1 (Page 2) - Different CCs for top 3 encoders in each row
SEND_IDS_BANK1 = ((64, 65, 66, 28, 67, 68, 69, 58), (70, 71, 72, 29, 73, 74, 75, 59))
PAN_IDS_BANK1 = [80, 81, 82, 30, 83, 84, 85, 60]

# CC Bank 2 (Page 3) - Another set of CCs for top 3 encoders
SEND_IDS_BANK2 = ((96, 97, 98, 28, 99, 100, 101, 58), (102, 103, 104, 29, 105, 106, 107, 59))
PAN_IDS_BANK2 = [112, 113, 114, 30, 115, 116, 117, 60]

# Map CC banks to their respective ID sets
CC_BANK_MAP = {
    0: {'send': SEND_IDS_BANK0, 'pan': PAN_IDS_BANK0},
    1: {'send': SEND_IDS_BANK1, 'pan': PAN_IDS_BANK1},
    2: {'send': SEND_IDS_BANK2, 'pan': PAN_IDS_BANK2}
}

class Colors(object):
    class DefaultButton(object):
        On = Color(127)
        Off = Color(0)
        Disabled = Color(0)

class MIDI_Mix(OptimizedControlSurface):
    def __init__(self, *a, **k):
        super(MIDI_Mix, self).__init__(*a, **k)
        self._current_cc_bank = 0  # Track current CC bank (0, 1, 2)
        with self.component_guard():
            self._skin = Skin(Colors)
            with inject(skin=(const(self._skin))).everywhere():
                self._create_controls()
                self._create_mixer()
                # Enable components after creation
                self._mixer.set_enabled(True)

    def _create_controls(self):
        self._sliders = make_button_row(chain(range(19, 32, 4), range(49, 62, 4)), make_slider, "Volume_Slider")
        self._rec_arm_buttons = make_button_row(range(3, 25, 3), make_button, "Record_Arm_Button")
        self._mute_buttons = make_button_row(range(1, 23, 3), make_button, "Mute_Button")
        self._solo_buttons = make_button_row(range(2, 24, 3), make_button, "Solo_Button")
        
        # Create encoders with initial CC bank 0 IDs
        self._send_encoders = self._create_send_encoders(SEND_IDS_BANK0)
        self._pan_encoders = self._create_pan_encoders(PAN_IDS_BANK0)
        
        self._bank_left_button = make_button(25, "Bank_Left_Button")
        self._bank_right_button = make_button(26, "Bank_Right_Button")
        self._solo_mode_button = make_button(27, "Solo_Mode_Button")
        self._master_slider = make_slider(62, "Master_Slider")

    def _create_send_encoders(self, send_ids):
        """Create send encoders with specified CC IDs"""
        return ButtonMatrixElement(rows=[
            [make_encoder(id, "Send_Encoder_B%d_R%d_C%d" % (self._current_cc_bank, row_index, id_index)) 
             for id_index, id in enumerate(row)] 
            for row_index, row in enumerate(send_ids)
        ])

    def _create_pan_encoders(self, pan_ids):
        """Create pan encoders with specified CC IDs"""
        return make_button_row(pan_ids, make_encoder, "Pan_Encoder_B%d" % self._current_cc_bank)

    def _update_encoders_for_cc_bank(self, cc_bank):
        """Update encoder CC values when switching CC banks"""
        if cc_bank == self._current_cc_bank or cc_bank not in CC_BANK_MAP:
            return
            
        old_cc_bank = self._current_cc_bank
        self._current_cc_bank = cc_bank
        
        # Temporarily disable mixer
        was_enabled = self._mixer.is_enabled()
        if was_enabled:
            self._mixer.set_enabled(False)
        
        # Get the appropriate CC sets for this bank
        send_ids = CC_BANK_MAP[cc_bank]['send']
        pan_ids = CC_BANK_MAP[cc_bank]['pan']
        
        # Store old controls for cleanup
        old_send_encoders = self._send_encoders
        old_pan_encoders = self._pan_encoders
        
        # Create new encoders with updated CCs
        self._send_encoders = self._create_send_encoders(send_ids)
        self._pan_encoders = self._create_pan_encoders(pan_ids)
        
        # Update the mixer's layer to use new controls
        if hasattr(self._mixer, '_layer'):
            # Update send controls
            self._mixer._layer.send_controls.control = self._send_encoders
            self._mixer.set_send_controls(self._send_encoders)
            
            # Update pan controls  
            self._mixer._layer.pan_controls.control = self._pan_encoders
            for index, strip in enumerate(self._mixer._channel_strips):
                if index < len(self._pan_encoders):
                    strip.set_pan_control(self._pan_encoders[index])
        
        # Re-enable mixer if it was enabled
        if was_enabled:
            self._mixer.set_enabled(True)
        
        # Update bank button LEDs
        if hasattr(self._mixer, '_update_bank_button_leds'):
            self._mixer._update_bank_button_leds()
        
        # Clean up old controls
        if old_send_encoders:
            old_send_encoders.disconnect()
        if old_pan_encoders:
            for encoder in old_pan_encoders:
                if hasattr(encoder, 'disconnect'):
                    encoder.disconnect()
        
        self.log_message("Switched from CC bank %d to CC bank %d" % (old_cc_bank, cc_bank))

    def _create_mixer(self):
        self._mixer = MixerComponent(
            parent_surface=self,  # Pass reference to parent surface
            num_tracks=NUM_TRACKS,
            is_enabled=False,
            invert_mute_feedback=True,
            layer=Layer(
                volume_controls=(self._sliders),
                pan_controls=(self._pan_encoders),
                send_controls=(self._send_encoders),
                bank_down_button=(self._bank_left_button),
                bank_up_button=(self._bank_right_button),
                arm_buttons=(self._rec_arm_buttons),
                solo_buttons=(self._solo_buttons),
                mute_buttons=(self._mute_buttons)
            )
        )
        self._mixer.master_strip().layer = Layer(volume_control=(self._master_slider))
        # Set initial bank button LEDs
        self._mixer._update_bank_button_leds()

    def _enable_components(self):
        with self.component_guard():
            for component in self.components:
                component.set_enabled(True)
        # Update LEDs after enabling
        if hasattr(self._mixer, '_update_bank_button_leds'):
            self._mixer._update_bank_button_leds()

    def _on_identity_response(self, midi_bytes):
        super(MIDI_Mix, self)._on_identity_response(midi_bytes)
        self._enable_components()

    def _on_handshake_successful(self):
        self._enable_components()

    def _product_model_id_byte(self):
        return 49

    def _send_dongle_challenge(self):
        pass

    def disconnect(self):
        """Clean disconnect"""
        super(MIDI_Mix, self).disconnect()