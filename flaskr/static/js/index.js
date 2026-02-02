import { handleNavbar, handleFlashButton } from "./base.js";
import { handleLoginPasswordVisibility } from "./auth.js";

document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM loaded");
  handleLoginPasswordVisibility();
  handleNavbar();
  handleFlashButton();
});
