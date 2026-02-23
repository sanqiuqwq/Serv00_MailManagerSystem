// Liquid Glass Effect for Buttons and Cards
// Based on Shu Ding's liquid-glass (https://github.com/shuding/liquid-glass)

(function() {
  'use strict';
  
  // Utility functions
  function smoothStep(a, b, t) {
    t = Math.max(0, Math.min(1, (t - a) / (b - a)));
    return t * t * (3 - 2 * t);
  }

  function length(x, y) {
    return Math.sqrt(x * x + y * y);
  }

  function roundedRectSDF(x, y, width, height, radius) {
    const qx = Math.abs(x) - width + radius;
    const qy = Math.abs(y) - height + radius;
    return Math.min(Math.max(qx, qy), 0) + length(Math.max(qx, 0), Math.max(qy, 0)) - radius;
  }

  function texture(x, y) {
    return { type: 't', x, y };
  }

  function generateId() {
    return 'liquid-glass-' + Math.random().toString(36).substr(2, 9);
  }

  class LiquidGlassEffect {
    constructor(element, options = {}) {
      this.element = element;
      this.options = options;
      this.id = generateId();
      this.canvasDPI = 1;
      this.mouse = { x: 0, y: 0 };
      this.mouseUsed = false;
      this.isActive = false;
      
      this.init();
    }

    init() {
      this.createElements();
      this.setupEventListeners();
    }

    createElements() {
      const rect = this.element.getBoundingClientRect();
      this.width = Math.ceil(rect.width);
      this.height = Math.ceil(rect.height);

      this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      this.svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      this.svg.setAttribute('width', '0');
      this.svg.setAttribute('height', '0');
      this.svg.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        pointer-events: none;
        z-index: 1;
      `;

      const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
      filter.setAttribute('id', `${this.id}_filter`);
      filter.setAttribute('filterUnits', 'userSpaceOnUse');
      filter.setAttribute('colorInterpolationFilters', 'sRGB');
      filter.setAttribute('x', '0');
      filter.setAttribute('y', '0');
      filter.setAttribute('width', this.width.toString());
      filter.setAttribute('height', this.height.toString());

      this.feImage = document.createElementNS('http://www.w3.org/2000/svg', 'feImage');
      this.feImage.setAttribute('id', `${this.id}_map`);
      this.feImage.setAttribute('width', this.width.toString());
      this.feImage.setAttribute('height', this.height.toString());

      this.feDisplacementMap = document.createElementNS('http://www.w3.org/2000/svg', 'feDisplacementMap');
      this.feDisplacementMap.setAttribute('in', 'SourceGraphic');
      this.feDisplacementMap.setAttribute('in2', `${this.id}_map`);
      this.feDisplacementMap.setAttribute('xChannelSelector', 'R');
      this.feDisplacementMap.setAttribute('yChannelSelector', 'G');
      this.feDisplacementMap.setAttribute('scale', '0');

      filter.appendChild(this.feImage);
      filter.appendChild(this.feDisplacementMap);
      defs.appendChild(filter);
      this.svg.appendChild(defs);

      this.canvas = document.createElement('canvas');
      this.canvas.width = this.width * this.canvasDPI;
      this.canvas.height = this.height * this.canvasDPI;
      this.canvas.style.display = 'none';

      this.context = this.canvas.getContext('2d');

      document.body.appendChild(this.svg);
      document.body.appendChild(this.canvas);

      this.element.style.backdropFilter = `url(#${this.id}_filter) blur(0.25px) contrast(1.1) brightness(1.02)`;
    }

    setupEventListeners() {
      this.element.addEventListener('mouseenter', () => {
        this.isActive = true;
        this.updateShader();
      });

      this.element.addEventListener('mouseleave', () => {
        this.isActive = false;
        this.feDisplacementMap.setAttribute('scale', '0');
      });

      this.element.addEventListener('mousemove', (e) => {
        if (!this.isActive) return;
        
        const rect = this.element.getBoundingClientRect();
        this.mouse.x = (e.clientX - rect.left) / rect.width;
        this.mouse.y = (e.clientY - rect.top) / rect.height;
        
        this.updateShader();
      });

      window.addEventListener('resize', () => {
        this.updateSize();
      });
    }

    updateSize() {
      const rect = this.element.getBoundingClientRect();
      this.width = Math.ceil(rect.width);
      this.height = Math.ceil(rect.height);
      
      this.canvas.width = this.width * this.canvasDPI;
      this.canvas.height = this.height * this.canvasDPI;
    }

    updateShader() {
      if (!this.isActive) return;

      const mouseProxy = new Proxy(this.mouse, {
        get: (target, prop) => {
          this.mouseUsed = true;
          return target[prop];
        }
      });

      this.mouseUsed = false;

      const w = this.width * this.canvasDPI;
      const h = this.height * this.canvasDPI;
      const data = new Uint8ClampedArray(w * h * 4);

      let maxScale = 0;
      const rawValues = [];

      for (let i = 0; i < data.length; i += 4) {
        const x = (i / 4) % w;
        const y = Math.floor(i / 4 / w);
        const pos = this.fragment(
          { x: x / w, y: y / h },
          mouseProxy
        );
        const dx = pos.x * w - x;
        const dy = pos.y * h - y;
        maxScale = Math.max(maxScale, Math.abs(dx), Math.abs(dy));
        rawValues.push(dx, dy);
      }

      maxScale *= 0.5;

      let index = 0;
      for (let i = 0; i < data.length; i += 4) {
        const r = rawValues[index++] / maxScale + 0.5;
        const g = rawValues[index++] / maxScale + 0.5;
        data[i] = r * 255;
        data[i + 1] = g * 255;
        data[i + 2] = 0;
        data[i + 3] = 255;
      }

      this.context.putImageData(new ImageData(data, w, h), 0, 0);
      this.feImage.setAttributeNS('http://www.w3.org/1999/xlink', 'href', this.canvas.toDataURL());
      this.feDisplacementMap.setAttribute('scale', Math.min((maxScale / this.canvasDPI), 20).toString());
    }

    fragment(uv, mouse) {
      const ix = uv.x - 0.5;
      const iy = uv.y - 0.5;
      
      const dx = uv.x - mouse.x;
      const dy = uv.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      const influence = smoothStep(0.5, 0, dist);
      
      const displacement = influence * 0.15;
      
      return texture(
        uv.x - dx * displacement,
        uv.y - dy * displacement
      );
    }

    destroy() {
      this.svg.remove();
      this.canvas.remove();
    }
  }

  function initLiquidGlass() {
    const buttons = document.querySelectorAll('.btn');
    const cards = document.querySelectorAll('.card');
    const jumbotrons = document.querySelectorAll('.jumbotron');
    const alerts = document.querySelectorAll('.alert');
    const modals = document.querySelectorAll('.modal-content');

    const elements = [...buttons, ...cards, ...jumbotrons, ...alerts, ...modals];

    elements.forEach((element, index) => {
      setTimeout(() => {
        new LiquidGlassEffect(element);
      }, index * 50);
    });

    console.log('Liquid Glass effect initialized for buttons and cards!');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLiquidGlass);
  } else {
    initLiquidGlass();
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          if (node.classList && node.classList.contains('modal-content')) {
            setTimeout(() => {
              new LiquidGlassEffect(node);
            }, 100);
          }
          const modals = node.querySelectorAll ? node.querySelectorAll('.modal-content') : [];
          modals.forEach((modal) => {
            setTimeout(() => {
              new LiquidGlassEffect(modal);
            }, 100);
          });
        }
      });
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  window.initLiquidGlass = initLiquidGlass;
})();
