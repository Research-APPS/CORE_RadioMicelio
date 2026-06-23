(function () {
  function eachDetails(root, fn) {
    root.querySelectorAll("details.taxonomy-branch").forEach(fn);
  }

  document.addEventListener("click", function (event) {
    if (event.target.closest(".taxonomy-node__link")) {
      event.stopPropagation();
      return;
    }

    var btn = event.target.closest("[data-taxonomy-action]");
    if (!btn) return;
    var tree = btn.closest(".taxonomy-page");
    if (!tree) return;
    var action = btn.getAttribute("data-taxonomy-action");
    if (action === "expand-all") {
      eachDetails(tree, function (d) { d.open = true; });
    } else if (action === "collapse-all") {
      eachDetails(tree, function (d) { d.open = false; });
    }
  });
})();
