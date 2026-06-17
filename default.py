import dbus
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()

_bus = dbus.SessionBus()

_ss = dbus.Interface(
    _bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver'),
    'org.freedesktop.ScreenSaver',
)

_pm = dbus.Interface(
    _bus.get_object('org.kde.Solid.PowerManagement', '/org/kde/Solid/PowerManagement'),
    'org.kde.Solid.PowerManagement',
)

_LOG = 'kde-dpms-inhibitor'


def _acquire_inhibit():
    try:
        cookie = _ss.Inhibit('Kodi', 'User active')
        xbmc.log(f'{_LOG}: inhibit acquired (cookie={cookie})', xbmc.LOGDEBUG)
        return cookie
    except dbus.DBusException as e:
        xbmc.log(f'{_LOG}: failed to acquire inhibit: {e}', xbmc.LOGWARNING)
        return None


def _release_inhibit(cookie):
    try:
        _ss.UnInhibit(cookie)
        xbmc.log(f'{_LOG}: inhibit released (cookie={cookie})', xbmc.LOGDEBUG)
    except dbus.DBusException as e:
        xbmc.log(f'{_LOG}: failed to release inhibit: {e}', xbmc.LOGWARNING)


def _wakeup():
    try:
        _pm.wakeup()
        xbmc.log(f'{_LOG}: wakeup sent', xbmc.LOGDEBUG)
    except dbus.DBusException as e:
        xbmc.log(f'{_LOG}: wakeup failed: {e}', xbmc.LOGWARNING)


monitor = xbmc.Monitor()

cookie = _acquire_inhibit()
prev_idle = xbmc.getGlobalIdleTime()
xbmc.log(f'{_LOG}: started (idle={prev_idle}s)', xbmc.LOGDEBUG)

while not monitor.abortRequested():
    poll_interval = int(ADDON.getSetting('poll_interval'))
    threshold = int(ADDON.getSetting('idle_threshold'))
    monitor.waitForAbort(poll_interval)

    idle = xbmc.getGlobalIdleTime()

    if idle < prev_idle:
        xbmc.log(f'{_LOG}: idle timer reset ({prev_idle}s -> {idle}s)', xbmc.LOGDEBUG)
        if cookie is None:
            _wakeup()
            cookie = _acquire_inhibit()
    elif idle >= threshold and cookie is not None:
        xbmc.log(f'{_LOG}: idle threshold reached ({idle}s >= {threshold}s), releasing inhibit', xbmc.LOGDEBUG)
        _release_inhibit(cookie)
        cookie = None

    prev_idle = idle

xbmc.log(f'{_LOG}: shutting down', xbmc.LOGDEBUG)
if cookie is not None:
    _release_inhibit(cookie)
