async function runSearch() {
    const query = document.getElementById("query").value
    let results = await window.pywebview.api.run_search(query)
    document.getElementById("results").innerText = JSON.stringify(results, null, 2)
}

async function loadConfig() {
    let cfg = await window.pywebview.api.get_config()
    console.log("Config loaded:", cfg)
}
loadConfig()
