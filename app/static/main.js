// const pageTopBtn = document.getElementById("page-top");

// window.addEventListener("scroll", () => {
//   if (window.scrollY > 300) {
//     pageTopBtn.classList.add("show");
//   } else {
//     pageTopBtn.classList.remove("show");
//   }
// });

// pageTopBtn.addEventListener("click", () => {
//   window.scrollTo({
//     top: 0,
//     behavior: "smooth"
//   });
// });

(() => {
  const timelineViewport = window.matchMedia("(max-width: 1296px)");

  const alignActiveTimelineYear = () => {
    const params = new URLSearchParams(window.location.search);

    if (!timelineViewport.matches || !params.has("year")) {
      return;
    }

    const activeYearLink = document.querySelector(
      ".portfolio-database-layout .timeline-year-link.is-active"
    );
    const yearList = activeYearLink?.closest(".timeline-year-list");

    if (!activeYearLink || !yearList) {
      return;
    }

    window.requestAnimationFrame(() => {
      const listRect = yearList.getBoundingClientRect();
      const activeRect = activeYearLink.getBoundingClientRect();
      const targetLeft =
        yearList.scrollLeft +
        activeRect.left -
        listRect.left -
        (yearList.clientWidth - activeYearLink.offsetWidth) / 2;

      yearList.scrollTo({
        left: Math.max(0, targetLeft),
        behavior: "auto",
      });

      const updatedActiveRect = activeYearLink.getBoundingClientRect();
      const targetTop =
        window.scrollY +
        updatedActiveRect.top -
        (window.innerHeight - updatedActiveRect.height) / 2;

      window.scrollTo({
        top: Math.max(0, targetTop),
        behavior: "auto",
      });
    });
  };

  window.addEventListener("DOMContentLoaded", alignActiveTimelineYear);
  window.addEventListener("pageshow", alignActiveTimelineYear);
})();
