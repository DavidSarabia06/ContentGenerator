
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("toggle");

  if (sidebar.classList.contains("collapsed")) {
    sidebar.classList.remove("collapsed");
    sidebar.classList.add("expanded");
    toggle.src="icons/colapsar_light.png"

  }
  else {
    sidebar.classList.remove("expanded");
    sidebar.classList.add("collapsed");
    toggle.src="icons/desplegar_light.png"
  }

}


