document.addEventListener('DOMContentLoaded', () => {
  const draw1 = document.getElementById('draw1')
  const draw10 = document.getElementById('draw10')
  const results = document.getElementById('results')
  const userStatus = document.getElementById('user_status')

  if (draw1) draw1.addEventListener('click', () => doDraw(1))
  if (draw10) draw10.addEventListener('click', () => doDraw(10))

  async function refreshProfile() {
    try {
      const r = await fetch('/api/profile')
      if (r.status === 200) {
        const data = await r.json()
        if (userStatus) userStatus.innerText = `${data.username} - ${data.currency} ₽`;
        const cost = window.PULL_COST || 100
        if (draw1) draw1.disabled = data.currency < cost
        if (draw10) draw10.disabled = data.currency < cost*10
      } else {
        if (userStatus) userStatus.innerText = 'Not logged in'
      }
    } catch (e) {
      if (userStatus) userStatus.innerText = 'Not logged in'
    }
  }

  async function doDraw(n) {
    results.innerText = 'Drawing...'
    try {
      const resp = await fetch(`/api/pool/${POOL_TAG}/draw`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({n}) })
      const data = await resp.json()
      if (data.results) {
        results.innerHTML = data.results.map(r => `<div>${r.name} (${r.rarity}★) ${r.featured?'<strong class="featured">FEATURED</strong>':''}</div>`).join('')
        // refresh profile to update currency
        await refreshProfile()
      } else if (data.error) {
        results.innerText = data.error
      }
    } catch (e) {
      results.innerText = 'Error: ' + e.message
    }
  }

  // try to fetch profile on load
  refreshProfile()
})
