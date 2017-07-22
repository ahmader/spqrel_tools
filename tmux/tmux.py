#! /usr/bin/env python
from libtmux import Server
from json import load
from logging import error, warn, info, debug, basicConfig, INFO, WARN
from pprint import pformat
from time import sleep
import signal
import os
import argparse
from psutil import Process, wait_procs

from datetime import datetime
basicConfig(level=INFO)


class TMux:

    def __init__(self, session_name="spqrel", configfile=None):
        self.server = Server()
        if self.server.has_session(session_name):
            self.session = self.server.find_where({
                "session_name": session_name
            })

            info('found running session %s on server' % session_name)
        else:
            info('starting new session %s on server' % session_name)
            self.session = self.server.new_session(session_name=session_name)
        if configfile:
            self.load_config(configfile)
        else:
            self.config = None

    def _on_terminate(self, proc):
        info("process {} terminated with exit code {}"
             .format(proc, proc.returncode))

    def _terminate(self, pid):
        procs = Process(pid).children()
        for p in procs:
            p.terminate()
        gone, still_alive = wait_procs(procs, timeout=1,
                                       callback=self._on_terminate)
        for p in still_alive:
            p.kill()

    def _get_children_pids(self, pid):
        return Process(pid).children(recursive=True)

    def load_config(self, filename="sample_config.json"):
        with open(filename) as data_file:
            self.config = load(data_file)

    def init(self):
        if not self.config:
            error('config file not loaded; call "load_config" first!')
        else:
            for win in self.config['windows']:
                window = self.session.find_where({
                    "window_name": win['name']
                })
                if window:
                    debug('window %s already exists' % win['name'])
                else:
                    debug('create window %s' % win['name'])
                    window = self.session.new_window(win['name'])
                exist_num_panes = len(window.list_panes())
                while exist_num_panes < len(win['panes']):
                    debug('new pane needed in window %s' % win['name'])
                    window.split_window(vertical=1)
                    exist_num_panes = len(window.list_panes())
                window.cmd('select-layout', 'tiled')

    def find_window(self, window_name):
        for win in self.config['windows']:
            if win['name'] == window_name:
                window = self.session.find_where({
                    "window_name": win['name']
                })
                window.select_window()
                return win, window

    def send_ctrlc(self, pane):
        datestr = datetime.now().strftime('%c')
        pane.cmd("send-keys", "", "C-c")
        pane.cmd("send-keys", "", "C-c")
        pane.cmd("send-keys", "", "C-c")
        pane.send_keys('# tmux-controller sent Ctrl-C at %s' % datestr,
                       enter=True, suppress_history=True)

    def is_running(self, window_name):
        winconf, window = self.find_window(window_name)
        if '_running' in winconf:
            return winconf['_running']
        else:
            return False


    def launch_window(self, window_name, enter=True):
        info('launch %s' % window_name)
        winconf, window = self.find_window(window_name)
        pane_no = 0
        datestr = datetime.now().strftime('%c')
        for cmd in winconf['panes']:
            pane = window.select_pane(pane_no)
            self.send_ctrlc(pane)
            pane.send_keys('# tmux-controller starts new command %s' % datestr,
                           enter=True, suppress_history=True)
            if 'init_cmd' in self.config:
                pane.send_keys(self.config['init_cmd'],
                               enter=enter, suppress_history=False)
            pane.send_keys(cmd, enter=enter, suppress_history=False)
            pane_no += 1
        winconf['_running'] = True

    def launch_all_windows(self):
        for winconf in self.config['windows']:
            self.launch_window(winconf['name'])

    def stop_all_windows(self):
        for winconf in self.config['windows']:
            self.stop_window(winconf['name'])

    def get_children_pids_all_windows(self):
        pids = []
        for winconf in self.config['windows']:
            pids.extend(
                self.get_children_pids_window(winconf['name'])
            )
        return pids

    def kill_all_windows(self):
        for winconf in self.config['windows']:
            self.kill_window(winconf['name'])

    def stop_window(self, window_name):
        info('stop %s' % window_name)
        winconf, window = self.find_window(window_name)
        self._stop_window(winconf, window)

    def _stop_window(self, winconf, window):
        pane_no = 0
        for cmd in winconf['panes']:
            pane = window.select_pane(pane_no)
            self.send_ctrlc(pane)
            pane_no += 1
        pids = self._get_pids_window(window)
        sleep(.1)
        for p in pids:
            self._terminate(p)
        winconf['_running'] = False

    def kill_window(self, window_name):
        info('terminate %s' % window_name)
        winconf, window = self.find_window(window_name)
#                       "-F '#{pane_active} #{pane_pid}")
        self._stop_window(winconf, window)
        pids = self._get_pids_window(window)
        for pid in pids:
            Process(pid).terminate()
        winconf['_running'] = False

    def list_windows(self):
        return [w['name'] for w in self.config['windows']]

    def get_pids_window(self, window_name):
        winconf, window = self.find_window(window_name)
        return self._get_pids_window(window)

    def _get_pids_window(self, window):
        r = window.cmd('list-panes',
                       "-F #{pane_pid}")
        return [int(p) for p in r.stdout]

    def get_children_pids_window(self, window_name):
        winconf, window = self.find_window(window_name)
        return self._get_children_pids_window(window)

    def _get_children_pids_window(self, window):
        winpids = self._get_pids_window(window)
        pids = []
        for pid in winpids:
            pids.extend(self._get_children_pids(pid))
        return [p.pid for p in pids]

    def is_running(self, window_name):
        winconf, window = self.find_window(window_name)
        pids = self._get_children_pids_window(window)
        return len(pids) > 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str,
                        default='spqrel-pepper-config.json',
                        help="JSON config file. see sample-config.json. Default: spqrel-pepper-config.json")
    parser.add_argument("--init", type=bool, default=True,
                        help="Should tmux be initialised? Default: True")
    parser.add_argument("--session", type=str,
                        default='spqrel',
                        help="The session that is controlled. Default: spqrel")

    subparsers = parser.add_subparsers(dest='cmd',
                                       help='sub-command help')
    parser_list = subparsers.add_parser('list', help='show windows')
    parser_launch = subparsers.add_parser('launch', help='launch window(s)')
    parser_launch.add_argument("--window", '-w', type=str,
                               default="",
                               help="Window to be launched. Default: ALL")
    parser_stop = subparsers.add_parser('stop', help='stop windows(s)')
    parser_stop.add_argument("--window", '-w', type=str,
                             default="",
                             help="Window to be stopped. Default: ALL")
    parser_relaunch = subparsers.add_parser('relaunch',
                                            help='relaunch windows(s)')
    parser_relaunch.add_argument("--window", '-w', type=str,
                                 default="",
                                 help="Window to be relaunched. Default: ALL")
    parser_kill = subparsers.add_parser('terminate', help='kill window(s)')
    parser_kill.add_argument("--window", '-w', type=str,
                             default="",
                             help="Window to be killed. Default: ALL")
    parser_pids = subparsers.add_parser('pids', help='pids of processes')
    parser_pids.add_argument(
        "--window", '-w', type=str,
        default="",
        help="Window for which PIDs are shown. Default: ALL")
    parser_pids = subparsers.add_parser(
        'running',
        help='returns true of there is a process running in the window')
    parser_pids.add_argument("--window", '-w', type=str,
                             required=True,
                             help="Window to be checked.")

    args = parser.parse_args()

    tmux = TMux(configfile=args.config)

    if (args.init):
        tmux.init()

    if args.cmd == 'list':
        print(pformat(tmux.list_windows()))
    elif args.cmd == 'launch':
        if args.window == '':
            tmux.launch_all_windows()
            pass
        else:
            tmux.launch_window(args.window)
    elif args.cmd == 'stop':
        if args.window == '':
            tmux.stop_all_windows()
        else:
            tmux.stop_window(args.window)
    elif args.cmd == 'relaunch':
        if args.window == '':
            tmux.stop_all_windows()
            sleep(1)
            tmux.launch_all_windows()
        else:
            tmux.stop_window(args.window)
            sleep(1)
            tmux.launch_window(args.window)
    elif args.cmd == 'terminate':
        if args.window == '':
            tmux.kill_all_windows()
        else:
            tmux.kill_window(args.window)
    elif args.cmd == 'running':
        print tmux.is_running(args.window)
    elif args.cmd == 'pids':
        if args.window == '':
            print(pformat(tmux.get_children_pids_all_windows()))
        else:
            print(pformat(tmux.get_children_pids_window(args.window)))


    # windows_to_launch = [
    #     'htop', 'navigation', 'speech', 'ui', 'pnp', 'dataset'
    # ]
    # for w in windows_to_launch:
    #     tmux.launch_window(w, True)
    #     sleep(1)
    # #sleep(8)
    # tmux.stop_all_windows()
    # tmux.terminate()
