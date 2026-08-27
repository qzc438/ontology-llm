/* Day and night modes.

   The mode follows the clock on the machine showing the page, and the reader can
   override it. The choice is one of three: "auto" follows the clock, "day" and
   "night" hold whichever was picked. It is remembered in localStorage, so it
   survives a reload and applies to every page of the interface.

   This file is loaded in <head> and applies the mode straight away, before the
   first paint, so a night reader never gets a white flash. */

(function () {
  "use strict";

  var STORAGE_KEY = "agent-om-theme";

  // night runs from 18.00 to 06.00 on the reader's own clock
  var NIGHT_FROM = 18;
  var NIGHT_UNTIL = 6;

  // how often "auto" re-checks the clock, so the page turns over at dusk
  // without needing a reload
  var CHECK_EVERY_MS = 60 * 1000;

  function modeForClock(now) {
    var hour = (now || new Date()).getHours();
    return (hour >= NIGHT_FROM || hour < NIGHT_UNTIL) ? "night" : "day";
  }

  function readChoice() {
    try {
      var stored = window.localStorage.getItem(STORAGE_KEY);
      return (stored === "day" || stored === "night" || stored === "auto")
        ? stored : "auto";
    } catch (error) {
      // private browsing can refuse storage; the clock still works
      return "auto";
    }
  }

  function writeChoice(choice) {
    try {
      window.localStorage.setItem(STORAGE_KEY, choice);
    } catch (error) {
      /* nothing to do, the choice just will not outlive the page */
    }
  }

  function apply(choice) {
    var mode = choice === "auto" ? modeForClock() : choice;
    var root = document.documentElement;
    root.setAttribute("data-theme", mode);
    root.setAttribute("data-theme-choice", choice);
    return mode;
  }

  // run immediately, before anything is painted
  apply(readChoice());

  // the button carries no words, so what it means and what it will do next are
  // in the title and aria-label instead
  var ORDER = ["auto", "day", "night"];

  var DESCRIPTION = {
    auto: "Colour mode follows the clock. Activate for day.",
    day: "Day mode. Activate for night.",
    night: "Night mode. Activate to follow the clock."
  };

  function wire() {
    var button = document.querySelector("[data-theme-control]");
    if (!button) return;

    function refresh() {
      var choice = readChoice();
      apply(choice);
      button.setAttribute("aria-label", DESCRIPTION[choice]);
      button.setAttribute("title", DESCRIPTION[choice]);
    }

    button.addEventListener("click", function () {
      var next = ORDER[(ORDER.indexOf(readChoice()) + 1) % ORDER.length];
      writeChoice(next);
      refresh();
    });

    refresh();

    // keep "auto" honest as the evening arrives
    window.setInterval(function () {
      if (readChoice() === "auto") refresh();
    }, CHECK_EVERY_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }

  // exposed so a page, or a test, can ask what the clock would choose
  window.AgentOMTheme = {
    apply: apply,
    readChoice: readChoice,
    modeForClock: modeForClock,
    nightFrom: NIGHT_FROM,
    nightUntil: NIGHT_UNTIL
  };
})();
