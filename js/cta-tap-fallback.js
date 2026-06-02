/**
 * CTA card tap fallback — iOS Chrome edition
 * ============================================================
 * Why this file exists
 * --------------------
 * The CSS-only fix in PR #4 (touch-action: manipulation +
 * pointer-events isolation + (hover: hover) and (pointer: fine)
 * gating) made CTA cards tappable on iPhone Safari, Android, and all
 * desktops. iPhone Chrome (and any iOS browser whose gesture stack
 * matches Chrome's behaviour) still swallowed short taps — long-press
 * on the same element correctly showed the iOS link context menu with
 * the right href, proving the link structure itself was never the
 * problem. iOS Chrome's gesture recogniser was just discarding the
 * click between the anchor and any click listener.
 *
 * Strategy
 * --------
 * Listen to the raw touch lifecycle (touchstart -> touchend) on the
 * CTA cards. If the touch was short and stayed in place — i.e. a
 * genuine tap rather than a scroll, swipe, or long-press — synthesise
 * the navigation ourselves via window.open / window.location.
 *
 * Browsers whose native click already fires never hit this path
 * because the click event arrives first; the click handler sees
 * alreadyHandled === false and lets the browser navigate normally.
 *
 * Defenses against double-navigation
 * ----------------------------------
 * - alreadyHandled flag guards both touchend and the synthetic click
 *   that iOS may still dispatch ~300 ms later.
 * - The touchend handler calls preventDefault() so the browser does
 *   not synthesise a click on top of our window.open.
 * - The click handler also calls preventDefault() if alreadyHandled
 *   is true (belt-and-braces).
 *
 * Scope
 * -----
 * Only attaches to elements matching `a.fb-video-cta-card`. Footer
 * links, header nav, and other anchors on the site are untouched.
 */
(function () {
  'use strict';

  function init() {
    // Selector covers every anchor we've explicitly opted in to the
    // touchend-based navigation safety net. Add new entries here when a
    // new CTA anchor is introduced that needs the same reliability.
    var cards = document.querySelectorAll('a.fb-video-cta-card, a.news-header-fb-btn');
    if (!cards.length) return;

    Array.prototype.forEach.call(cards, function (card) {
      var touchStartTime = 0;
      var touchStartX = 0;
      var touchStartY = 0;
      var alreadyHandled = false;

      card.addEventListener('touchstart', function (e) {
        if (!e.touches || !e.touches.length) return;
        touchStartTime = Date.now();
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        alreadyHandled = false;
      }, { passive: true });

      card.addEventListener('touchend', function (e) {
        if (alreadyHandled) return;
        if (!e.changedTouches || !e.changedTouches.length) return;

        var duration = Date.now() - touchStartTime;
        var endX = e.changedTouches[0].clientX;
        var endY = e.changedTouches[0].clientY;
        var deltaX = Math.abs(endX - touchStartX);
        var deltaY = Math.abs(endY - touchStartY);

        // Tap heuristic:
        //   - under 500 ms (anything longer is the long-press path that
        //     iOS already handles correctly via its context menu)
        //   - moved less than 10 px in either axis (anything more is a
        //     scroll or swipe, not a tap)
        var isTap = duration < 500 && deltaX < 10 && deltaY < 10;
        if (!isTap) return;

        var href = card.getAttribute('href');
        if (!href) return;

        // Mark handled BEFORE doing anything else so any racing click
        // event (which iOS may still dispatch after touchend) sees the
        // flag and bails out.
        alreadyHandled = true;
        e.preventDefault();

        var target = card.getAttribute('target') || '_self';
        if (target === '_blank') {
          // rel="noopener noreferrer" semantics — explicit, not from the
          // anchor's rel attribute, because window.open doesn't read it.
          window.open(href, '_blank', 'noopener,noreferrer');
        } else {
          window.location.href = href;
        }
      });

      // Desktop and Safari path: native click arrives, alreadyHandled
      // is still false, browser navigates normally. We don't interfere.
      // Only block the click if we already navigated via touchend, to
      // prevent the double-fire that opens two tabs.
      card.addEventListener('click', function (e) {
        if (alreadyHandled) {
          e.preventDefault();
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // Script was loaded with defer (so DOM is ready) or after
    // DOMContentLoaded fired — call init immediately.
    init();
  }
})();
