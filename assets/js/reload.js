// reload the current page based on file changes

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

function reload_page() {
  location.reload(true)
}

const back_off_times = [200, 500, 1000, 2000, 2000, 2000, 5000, 5000, 5000, 5000, 30000, 30000]

async function wait_for_server (to_run) {
  for (let back_off of back_off_times) {
    try {
      const r = await fetch('/.reload/up/')
      if (r.status !== 200) {
        console.debug(`unexpected response from '/.reload/up/': ${r.status}, waiting ${back_off} and trying again...`)
        await sleep(back_off)
        continue
      }
      await r.text()
    } catch (error) {
      // generally TypeError: failed to fetch
      console.debug(`failed to connect to '/.reload/up/', waiting ${back_off} and trying again...`)
      await sleep(back_off)
      continue
    }
    to_run()
    return
  }
  console.warn('page reload timed out, could not connect')
}

class ReloadWebsocket {
  constructor() {
    this._socket = null
    this.connect()
    this._connected = false
    this._clear_connected = null
  }

  connect = () => {
    this._connected = false
    const proto = location.protocol.replace('http', 'ws')
    const url = `${proto}//${window.location.host}/.reload/ws/`
    console.debug(`websocket connecting to "${url}"...`)
    try {
      this._socket = new WebSocket(url)
    } catch (error) {
      console.warn('ws connection error', error)
      this._socket = null
      return
    }

    state_badge(true)
    this._socket.onclose = this._on_close
    this._socket.onerror = this._on_error
    this._socket.onmessage = this._on_message
    this._socket.onopen = this._on_open
  }

  _on_open = () => {
    console.debug('websocket open')
    setTimeout(() => {
      this._connected = true
    }, 1000)
  }

  _on_message = event => {
    if (event.data !== 'reload') {
      console.warn('unexpected websocket message:', event)
      return
    }
    if (this._connected) {
      console.debug('files changed, reloading')
      state_badge(false)
      wait_for_server(reload_page)
    }
  }

  _on_error = event => {
    console.debug('websocket error', event)
    clearInterval(this._clear_connected)
  }

  _on_close = event => {
    clearInterval(this._clear_connected)
    if (this._connected) {
      // slight delay so this doesn't run as the page is manually reloaded
      setTimeout(() => {
        console.debug('websocket closed, prompting reload')
        state_badge(false)
        wait_for_server(reload_page)
      }, 100)
    } else {
      console.debug('websocket closed, reconnecting in 2s...', event)
      setTimeout(this.connect, 2000)
    }
  }
}

function state_badge(connected) {
  const el = document.getElementById('connection-state')
  if (connected) {
    el.classList.add('badge-success')
    el.classList.remove('badge-warning')
    el.innerText = 'connected'
    el.title = 'connected to watch server'
  } else {
    el.classList.add('badge-warning')
    el.classList.remove('badge-success')
    el.innerText = 'not connected'
    el.title = 'not connected to watch server, reconnecting...'

  }
}

wait_for_server(() => {
  window.dev_reloader = new ReloadWebsocket()
})

