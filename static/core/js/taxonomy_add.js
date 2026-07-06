(function () {
  const form = document.getElementById("taxonomy-add-form");
  const script = document.querySelector('script[data-add-url]');
  if (!form || !script) return;

  const parentInput = document.getElementById("taxonomy-add-parent");
  const labelInput = document.getElementById("taxonomy-add-label");
  const labelEl = form.querySelector(".taxonomy-add-form__label");

  function openForm(parentUuid, parentLabel) {
    parentInput.value = parentUuid || "";
    labelEl.textContent = parentLabel
      ? `Nueva clase dentro de «${parentLabel}»`
      : "Nueva clase de primer nivel";
    form.classList.remove("taxonomy-add-form--hidden");
    labelInput.value = "";
    labelInput.focus();
  }

  function closeForm() {
    form.classList.add("taxonomy-add-form--hidden");
    parentInput.value = "";
    labelInput.value = "";
  }

  document.querySelectorAll("[data-taxonomy-add-root]").forEach((btn) => {
    btn.addEventListener("click", () => openForm("", ""));
  });

  document.querySelectorAll(".taxonomy-add-btn").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openForm(btn.dataset.parentUuid || "", btn.dataset.parentLabel || "");
    });
  });

  const cancel = form.querySelector("[data-taxonomy-add-cancel]");
  if (cancel) cancel.addEventListener("click", closeForm);
})();
