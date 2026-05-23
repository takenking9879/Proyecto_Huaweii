(function () {
    const overlay = document.createElement('div');
    overlay.id = 'card-expand-overlay';
    document.body.appendChild(overlay);

    let expandedCard = null;
    let originalRect = null;
    let savedHeights  = [];
    let isAnimating   = false;

    function resizePlots(card) {
        card.querySelectorAll('.js-plotly-plot').forEach(function (plot) {
            if (window.Plotly) Plotly.Plots.resize(plot);
        });
    }

    function stretchCharts(card) {
        savedHeights = [];
        const labelEl = card.querySelector('.chart-label');
        const labelH  = labelEl ? (labelEl.offsetHeight + 8) : 40;
        const bodyEl  = card.querySelector('.card-body');
        const padT    = bodyEl ? parseFloat(window.getComputedStyle(bodyEl).paddingTop)    : 6;
        const padB    = bodyEl ? parseFloat(window.getComputedStyle(bodyEl).paddingBottom) : 10;
        const availH  = Math.floor(card.offsetHeight - labelH - padT - padB - 8);

        /* Dash renders dcc.Graph as <div class="dash-graph" style="height:Npx"> */
        card.querySelectorAll('.dash-graph').forEach(function (el) {
            savedHeights.push({ el: el, h: el.style.height });
            el.style.height = availH + 'px';
        });

        /* Give browser a frame to apply the new height, then let Plotly re-layout */
        setTimeout(function () { resizePlots(card); }, 60);
    }

    function restoreCharts() {
        savedHeights.forEach(function (item) {
            item.el.style.height = item.h;
        });
        savedHeights = [];
    }

    function expand(card) {
        if (isAnimating) return;
        isAnimating = true;

        originalRect = card.getBoundingClientRect();

        card.style.position   = 'fixed';
        card.style.top        = originalRect.top  + 'px';
        card.style.left       = originalRect.left + 'px';
        card.style.width      = originalRect.width  + 'px';
        card.style.height     = originalRect.height + 'px';
        card.style.zIndex     = '1000';
        card.style.margin     = '0';
        card.style.transition = 'none';

        overlay.style.display    = 'block';
        overlay.style.opacity    = '0';
        overlay.style.transition = 'opacity 300ms ease';

        card.offsetHeight; // force reflow
        overlay.style.opacity = '1';

        card.style.transition = [
            'top 320ms cubic-bezier(0.4, 0, 0.2, 1)',
            'left 320ms cubic-bezier(0.4, 0, 0.2, 1)',
            'width 320ms cubic-bezier(0.4, 0, 0.2, 1)',
            'height 320ms cubic-bezier(0.4, 0, 0.2, 1)',
            'border-radius 320ms cubic-bezier(0.4, 0, 0.2, 1)',
            'box-shadow 320ms ease'
        ].join(', ');

        requestAnimationFrame(function () {
            card.style.top          = '4vh';
            card.style.left         = '4vw';
            card.style.width        = '92vw';
            card.style.height       = '92vh';
            card.style.borderRadius = '20px';
            card.style.boxShadow    = '0 0 60px rgba(0,0,0,0.6)';
            card.style.overflow     = 'hidden';
        });

        card.addEventListener('transitionend', function done(e) {
            if (e.propertyName !== 'width') return;
            card.removeEventListener('transitionend', done);
            isAnimating  = false;
            expandedCard = card;
            stretchCharts(card);
        });
    }

    function collapse() {
        if (!expandedCard || isAnimating) return;
        isAnimating = true;

        const card = expandedCard;
        expandedCard = null;

        restoreCharts();

        card.style.top          = originalRect.top  + 'px';
        card.style.left         = originalRect.left + 'px';
        card.style.width        = originalRect.width  + 'px';
        card.style.height       = originalRect.height + 'px';
        card.style.borderRadius = '';
        card.style.boxShadow    = '';

        overlay.style.opacity = '0';

        card.addEventListener('transitionend', function done(e) {
            if (e.propertyName !== 'width') return;
            card.removeEventListener('transitionend', done);
            ['position','top','left','width','height','zIndex',
             'margin','transition','borderRadius','boxShadow','overflow'
            ].forEach(function (p) { card.style[p] = ''; });

            overlay.style.display    = 'none';
            overlay.style.transition = '';
            overlay.style.opacity    = '';
            isAnimating = false;
            resizePlots(card);
        });
    }

    overlay.addEventListener('click', collapse);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') collapse();
    });

    document.addEventListener('click', function (e) {
        const card = e.target.closest('.card-expandable');
        if (!card) return;
        /* Don't expand when interacting with controls */
        if (e.target.closest('.rc-slider, .Select, .dropdown-hw, button, input, select, a')) return;
        if (card === expandedCard) collapse();
        else if (!expandedCard) expand(card);
    });
})();
