document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".swap-model").forEach(el => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const path = el.getAttribute("data-model");
      const mv = document.getElementById("fmh-viewer");
      if (mv) mv.setAttribute("src", path);
    });
  });
});
