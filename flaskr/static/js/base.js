//Navbar button
export function handleNavbar() {
  const openMenu = document.getElementById("open-menu");
  const closeMenu = document.getElementById("close-menu");
  const navLinks = document.getElementById("mobile-navLinks");
  const openMenuHandler = () => {
    navLinks.classList.remove("-translate-x-full")
    navLinks.classList.add("translate-x-0")
  }

  const closeMenuHandler = () => {
    navLinks.classList.remove("translate-x-0")
    navLinks.classList.add("-translate-x-full")
  }

  openMenu.addEventListener("click", openMenuHandler);
  closeMenu.addEventListener("click", closeMenuHandler);
}

//Flash button
export function handleFlashButton() {
  const closeFlash = document.getElementById("close-flash");
  const flashElement = document.getElementById("flash-element");

  if (!flashElement) return;


  const removeFlashElement = () => {
    flashElement.classList.remove("translate-y-32", "opacity-100");
    flashElement.classList.add("opacity-0");

    setTimeout(() => {
      flashElement.remove();
    }, 500);
  }


  requestAnimationFrame(() => {
    flashElement.classList.remove("opacity-0");
    flashElement.classList.add("translate-y-32", "opacity-100");

    setTimeout(() => {
      removeFlashElement();
    }, 5000)
  })

  if (!closeFlash) return;

  closeFlash.addEventListener("click", () => {
    removeFlashElement();
  })
}
