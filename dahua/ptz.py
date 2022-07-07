#!/usr/bin/env python3
from re import compile
from requests import get
from requests.auth import HTTPDigestAuth

RGX_PRESET = compile(r'^presets\[(?P<index>\d+)]\.(?P<key>\w+)=(?P<value>.+)$')
RGX_IS_ARRAY = compile(r'^(?P<subcommand>.*)\[\d]$')
RGX_SPLIT_COMMAND = compile(r'^status\.(?P<body>.*)=(?P<value>.*)$')
RGX_RELATIVE_COORDINATES_VALUE = compile(r'^rect\[\d]=(?P<value>\d+)$')


class PTZ:
    def __init__(self, ip, channel, username, password):
        self._ip = ip
        self._channel = channel
        self._username = username
        self._password = password

    def go_to(self, x_position, y_position, zoom_in_multiple, speed):
        # x_position: X position from 'Position' not 'ABSPosition'
        # y_position: Y position
        # zoom_in_multiple: 0.0 - 128.0
        # speed: 1 - 8
        self._go_to_abs_position(x_position, y_position, zoom_in_multiple, speed)

    @property
    def position(self):  # Returns current position
        return self.status['Postion']

    def _go_to_position(self, horizontal_position, vertical_position, zoom_change):  # Go to specific position
        self.request('ptz', action='start', code='Position', channel=self._channel,
                     arg1=horizontal_position, arg2=vertical_position, arg3=zoom_change, arg4=0)

    def _go_to_abs_position(self, horizontal_angle, vertical_angle, zoom_in_multiple, speed):  # Go to absolute position
        self.request('ptz', action='start', code='PositionABS', channel=self._channel,
                     arg1=horizontal_angle, arg2=vertical_angle, arg3=zoom_in_multiple, arg4=speed)

    @property
    def status(self):
        def normalize_value(_subcommand, _value):
            int_values = (
                'ActionID',
                'PresetID',
                'ZoomValue',
                'AbsPosition',
                'ZoomMapValue',
                'FocusMapValue',
            )
            float_values = (
                'Postion',
                'IrisValue',
                'FocusPosition',
            )
            if _subcommand in int_values:
                return int(_value)
            elif _subcommand in float_values:
                return float(_value)
            return _value

        data = dict()
        response = self.request('ptz', action='getStatus', channel=self._channel, return_data=True)
        for line in response.split():
            line = line.strip()

            match = RGX_SPLIT_COMMAND.match(line)
            groups = match.groupdict()

            body = groups['body']
            value = groups['value']

            is_array = RGX_IS_ARRAY.match(body)
            subcommands = body.split('.')
            n_subcommands = len(subcommands)

            # single subcommand
            if n_subcommands == 1:
                subcommand, = subcommands
                # is_array['subcommand'] use the subcommand name without the [index]
                if is_array:
                    if is_array['subcommand'] not in data:
                        data[is_array['subcommand']] = []
                    normalized_value = normalize_value(is_array['subcommand'], value)
                    data[is_array['subcommand']].append(normalized_value)
                    continue
                # it's not an array
                normalized_value = normalize_value(subcommand, value)
                data[subcommand] = normalized_value
                continue

            # more than one subcommand
            prev_subcommand = data
            for i, subcommand in enumerate(subcommands):
                # assign value to last subcmomand
                if i == n_subcommands - 1:
                    if is_array:
                        if is_array['subcommand'] not in prev_subcommand:
                            prev_subcommand[is_array['subcommand']] = []
                        normalized_value = normalize_value(is_array['subcommand'], value)
                        prev_subcommand[is_array['subcommand']].append(normalized_value)
                        continue
                    normalized_value = normalize_value(subcommand, value)
                    prev_subcommand[subcommand] = normalized_value
                    continue
                # create dict next subcommand
                prev_subcommand[subcommand] = dict()
                prev_subcommand = prev_subcommand[subcommand]
        return data

    def zoom_in(self):  # Max zoom in
        self._zoom('ZoomTele')

    def zoom_out(self):  # Max zoom out
        self._zoom('ZoomWide')

    def _zoom(self, zoom_type):
        self.request('ptz', action='start', code=zoom_type, channel=self._channel, arg1=0, arg2=0, arg3=0, arg4=0)

    def move(self, horizontal_speed, vertical_speed, zoom_speed, timeout):
        assert 0 < timeout <= 3600, 'The maximum timeout value is 3600 seconds'
        assert -100 <= zoom_speed <= 100, 'zoom speed, range is [-100—100]'
        assert -8 <= vertical_speed <= 8, 'vertical speed, range is [-8 - 8]'
        assert -8 <= horizontal_speed <= 8, 'horizontal speed, range is [-8 - 8]'

        self.request('ptz', action='start', code='Continuously', channel=self._channel,
                     arg1=horizontal_speed, arg2=vertical_speed, arg3=zoom_speed, arg4=timeout)

    def stop(self):
        self.request('ptz', action='stop', code='Continuously', channel=self._channel,
                     arg1=0, arg2=0, arg3=0, arg4=0)

    def request(self, resource, return_data=False, **kwargs):
        url = f'http://{self._ip}/cgi-bin/{resource}.cgi'
        response = get(url, auth=HTTPDigestAuth(self._username, self._password), params=kwargs)

        if return_data:
            return response.text

        assert response.text.strip() == 'OK', response.text
