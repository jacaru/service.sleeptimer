# -*- coding: utf-8 -*-

""" Service Sleep Timer  (c)  2015 enen92, Solo0815

# This program is free software; you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation;
# either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program;
# if not, see <http://www.gnu.org/licenses/>.


"""

import time
import datetime
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import json
import os

msgdialogprogress = xbmcgui.DialogProgress()

addon_id = 'service.sleeptimer'
selfAddon = xbmcaddon.Addon(addon_id)
datapath = xbmc.translatePath(selfAddon.getAddonInfo('profile'))
addonfolder = xbmc.translatePath(selfAddon.getAddonInfo('path'))
debug_enable = selfAddon.getSetting('debug_mode')

__version__ = selfAddon.getAddonInfo('version')
check_time = selfAddon.getSetting('check_time')
check_time_next = int(selfAddon.getSetting('check_time_next'))
time_to_wait = int(selfAddon.getSetting('waiting_time_dialog'))
audiochange = selfAddon.getSetting('audio_change')
muteVol = int(selfAddon.getSetting('mute_volume'))
audiointervallength = int(selfAddon.getSetting('audio_interval_length'))
global audio_enable
audio_enable = str(selfAddon.getSetting('audio_enable'))
video_enable = str(selfAddon.getSetting('video_enable'))
max_time_audio = int(selfAddon.getSetting('max_time_audio'))
max_time_video = int(selfAddon.getSetting('max_time_video'))
enable_screensaver = selfAddon.getSetting('enable_screensaver')
custom_cmd = selfAddon.getSetting('custom_cmd')
cmd = selfAddon.getSetting('cmd')

# Functions:
def translate(text):
    return selfAddon.getLocalizedString(text).encode('utf-8')

def _log( message, isDebug ):
    if isDebug == 'true':
        xbmc.log(addon_id + ": " + str(message), level=xbmc.LOGDEBUG)
    else:
        xbmc.log(addon_id + ": " + str(message), level=xbmc.LOGINFO)

def debug( message ):
    _log(message, debug_enable)

def info( message ):
    _log(message, False)

# print the actual playing file in DEBUG-mode
def print_act_playing_file():
    actPlayingFile = xbmc.Player().getPlayingFile()
    debug (str(actPlayingFile))

# wait for abort - xbmc.sleep or time.sleep doesn't work
# and prevents Kodi from exiting
def do_next_check( iTimeToWait ):
    debug ( "DEBUG: next check in " + str(iTimeToWait) + " min" )
    if xbmc.Monitor().waitForAbort(int(iTimeToWait)*60):
        exit()

def get_kodi_time():
    am_pm = xbmc.getInfoLabel('System.Time(xx)').lower()
    system_time = xbmc.getInfoLabel('System.Time(hh:mm)')
    hour = system_time.split(':')[0]
    minute = system_time.split(':')[1]
    if am_pm == 'pm':
        hour = int(hour) + 12
    time_string = str(hour) + str(minute)
    return int(time_string)

def should_i_supervise(kodi_time,supervise_start_time,supervise_end_time):
    if selfAddon.getSetting('supervision_mode') == '0' or debug == 'true':
        return True
    else:
        if supervise_start_time == 0 and supervise_end_time == 0:
            return True
        elif kodi_time > supervise_start_time:
            if supervise_end_time > supervise_start_time:
                if kodi_time < supervise_end_time:
                    return True
                else:
                    return False
            else:
                supervise_end_time += 2400
                if kodi_time < supervise_end_time:
                    return True
                else:
                    return False
        else:
            if kodi_time < supervise_end_time:
                return True
            else:
                return False

class service:
    def __init__(self):
        FirstCycle = True
        next_check = False
        monitor = xbmc.Monitor()

        while not monitor.abortRequested():
            kodi_time = get_kodi_time()
            try:
                supervise_start_time = int(selfAddon.getSetting('hour_start_sup').split(':')[0]+selfAddon.getSetting('hour_start_sup').split(':')[1])
            except: supervise_start_time = 0
            try:
                supervise_end_time = int(selfAddon.getSetting('hour_end_sup').split(':')[0]+selfAddon.getSetting('hour_end_sup').split(':')[1])
            except: supervise_end_time = 0
            proceed = should_i_supervise(kodi_time,supervise_start_time,supervise_end_time)
            if proceed:
                if FirstCycle:
                    # Variables:
                    enable_audio = audio_enable
                    enable_video = video_enable
                    maxaudio_time_in_minutes = max_time_audio
                    maxvideo_time_in_minutes = max_time_video
                    iCheckTime = check_time

                    info ( "started ... (" + str(__version__) + ")" )
                    debug ( "################################################################" )
                    debug ( "Settings in Kodi:" )
                    debug ( "enable_audio: " + enable_audio )
                    debug ( "maxaudio_time_in_minutes: " + str(maxaudio_time_in_minutes) )
                    debug ( "enable_video: " + str(enable_video) )
                    debug ( "maxvideo_time_in_minutes: " + str(maxvideo_time_in_minutes) )
                    debug ( "check_time: " + str(iCheckTime) )
                    debug ( "Supervision mode: Always")
                    debug ( "################################################################" )

                    # wait 15s before start to let Kodi finish the intro-movie
                    if monitor.waitForAbort(15):
                        break

                    max_time_in_minutes = -1
                    idle_time_since_cancelled = 0
                    FirstCycle = False

                idle_time = xbmc.getGlobalIdleTime()
                idle_time_in_minutes = int(idle_time)/60

                if xbmc.Player().isPlaying():

                    if xbmc.Player().isPlayingAudio():
                        if enable_audio == 'true':
                            debug ( "enable_audio is true" )
                            print_act_playing_file()
                            what_is_playing = "audio"
                            max_time_in_minutes = maxaudio_time_in_minutes
                        else:
                            debug ( "Player is playing Audio, but check is disabled" )
                            do_next_check(iCheckTime)
                            continue

                    elif xbmc.Player().isPlayingVideo():
                        if enable_video == 'true':
                            debug ( "enable_video is true" )
                            print_act_playing_file()
                            what_is_playing = "video"
                            max_time_in_minutes = maxvideo_time_in_minutes
                        else:
                            debug ( "Player is playing Video, but check is disabled" )
                            do_next_check(iCheckTime)
                            continue

                    ### ToDo:
                    # expand it with RetroPlayer for playing Games!!!

                    else:
                        debug ( "Player is playing, but no Audio or Video" )
                        print_act_playing_file()
                        what_is_playing = "other"
                        do_next_check(iCheckTime)
                        continue

                    # only display the Progressdialog, if audio or video is enabled AND idle limit is reached

                    # Check if what_is_playing is not "other" and idle time exceeds limit
                    total_idle_time = idle_time_in_minutes + idle_time_since_cancelled
                    if ( what_is_playing != "other" and total_idle_time >= max_time_in_minutes ):

                        info ( "idle_time exceeds max allowed. Display Progressdialog" )
                        info ( "what_is_playing: " + str(what_is_playing) )
                        info ( "idle_time: '" + str(idle_time) + "s'; idle_time_in_minutes: '" + str(idle_time_in_minutes) + "'" )
                        info ( "idle_time_since_cancelled: '" + str(idle_time_since_cancelled) + "m" )
                        info ( "total_idle_time: '" + str(total_idle_time) + "m" )
                        info ( "max_time_in_minutes: " + str(max_time_in_minutes) )

                        ret = msgdialogprogress.create(translate(30000),translate(30001))
                        secs=0
                        percent=0
                        # use the multiplier 100 to get better %/calculation
                        increment = 100*100 / time_to_wait
                        cancelled = False
                        while secs < time_to_wait:
                            secs = secs + 1
                            # divide with 100, to get the right value
                            percent = increment*secs/100
                            secs_left = str((time_to_wait - secs))
                            remaining_display = str(secs_left) + " seconds left."
                            msgdialogprogress.update(int(percent),translate(30001))
                            xbmc.sleep(1000)
                            if (msgdialogprogress.iscanceled()):
                                cancelled = True
                                debug ( "DEBUG: Progressdialog cancelled" )
                                break
                        if cancelled == True:
                            iCheckTime = check_time_next
                            idle_time_since_cancelled += idle_time_in_minutes
                            info ( "Progressdialog cancelled, next check in " + str(iCheckTime) + " min" )
                            # set next_check, so that it opens the dialog after "iCheckTime"
                            next_check = True
                            msgdialogprogress.close()
                        else:
                            info ( "Progressdialog not cancelled: stopping Player" )
                            msgdialogprogress.close()
                            next_check = False
                            iCheckTime = check_time
                            idle_time_since_cancelled=0

                            # softmute audio before stop playing
                            # get actual volume
                            if audiochange == 'true':
                                resp = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Application.GetProperties", "params": { "properties": [ "volume"] }, "id": 1}')
                                dct = json.loads(resp)

                                if ("result" in dct) and ("volume" in dct["result"]):
                                    curVol = dct["result"]["volume"]

                                    for i in range(curVol - 1, muteVol - 1, -1):
                                        xbmc.executebuiltin('SetVolume(%d,showVolumeBar)' % (i))
                                        # move down slowly ((total mins / steps) * ms in a min)
                                        # (curVol-muteVol) runs the full timer where a user might control their volume via kodi instead of cutting it short when assuming a set volume of 100%
                                        xbmc.sleep(round(audiointervallength / (curVol - muteVol) * 60000))

                            # stop player anyway
                            monitor.waitForAbort(5) # wait 5s before stopping
                            xbmc.executebuiltin('PlayerControl(Stop)')

                            if audiochange == 'true':
                                monitor.waitForAbort(2) # wait 2s before changing the volume back
                                if ("result" in dct) and ("volume" in dct["result"]):
                                    curVol = dct["result"]["volume"]
                                    # we can move upwards fast, because there is nothing playing
                                    xbmc.executebuiltin('SetVolume(%d,showVolumeBar)' % (curVol))

                            if enable_screensaver == 'true':
                                debug ( "Activating screensaver" )
                                xbmc.executebuiltin('ActivateScreensaver')

                            # Run a custom cmd after playback is stopped
                            if custom_cmd == 'true':
                                debug ( "Running custom script" )
                                os.system(cmd)
                    else:
                        debug ( "Playing the stream, time does not exceed max limit" )
                        debug ( "what_is_playing: " + str(what_is_playing) )
                        debug ( "idle_time: '" + str(idle_time) + "s'; idle_time_in_minutes: '" + str(idle_time_in_minutes) + "'" )
                        debug ( "idle_time_since_cancelled: '" + str(idle_time_since_cancelled) + "m" )
                        debug ( "total_idle_time: '" + str(total_idle_time) + "m" )
                        debug ( "max_time_in_minutes: " + str(max_time_in_minutes) )
                else:
                    debug ( "Not playing any media file" )
                    # reset max_time_in_minutes
                    max_time_in_minutes = -1

                do_next_check(iCheckTime)
                monitor.waitForAbort(1)

service()
