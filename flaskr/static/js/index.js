import { handleNavbar, handleFlashButton } from "./base.js";
import { handleLoginPasswordVisibility, handleRegisterPasswordVisibility } from "./auth.js";

document.addEventListener('DOMContentLoaded', () => {
  handleLoginPasswordVisibility();
  handleRegisterPasswordVisibility();
  handleNavbar();
  handleFlashButton();
  console.log("DOM loaded");
});
