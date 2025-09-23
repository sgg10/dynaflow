(function (global) {
  const TEXT_ELEMENT = "__text__";
  const Fragment = Symbol("Fragment");

  class ComponentInstance {
    constructor(type, key) {
      this.type = type;
      this.key = key;
      this.hooks = [];
      this.hookIndex = 0;
      this.pendingEffects = [];
    }
  }

  const instances = new Map();
  let currentInstance = null;
  let rootElement = null;
  let rootContainer = null;
  let renderScheduled = false;
  let visitedInstances = new Set();
  let queuedEffects = [];

  function createElement(type, props, ...children) {
    const normalized = [];
    const rawChildren = (props && props.children) || [];
    const list = children.length ? children : Array.isArray(rawChildren) ? rawChildren : [rawChildren];
    for (const child of list.flat()) {
      if (child === false || child === true || child == null) {
        continue;
      }
      if (typeof child === "object") {
        normalized.push(child);
      } else {
        normalized.push(createTextElement(child));
      }
    }
    const cleanProps = Object.assign({}, props || {});
    delete cleanProps.children;
    return {
      type: type === Fragment ? Fragment : type,
      props: Object.assign(cleanProps, { children: normalized })
    };
  }

  function createTextElement(value) {
    return {
      type: TEXT_ELEMENT,
      props: { nodeValue: value == null ? "" : String(value), children: [] }
    };
  }

  function render(element, container) {
    rootElement = element;
    rootContainer = container;
    scheduleRender();
  }

  function scheduleRender() {
    if (renderScheduled) {
      return;
    }
    renderScheduled = true;
    queueMicrotask(() => {
      renderScheduled = false;
      performRender();
    });
  }

  function performRender() {
    if (!rootContainer || !rootElement) {
      return;
    }
    visitedInstances = new Set();
    queuedEffects = [];
    while (rootContainer.firstChild) {
      rootContainer.removeChild(rootContainer.firstChild);
    }
    renderNode(rootElement, rootContainer, "root");
    cleanupUnusedInstances();
    runQueuedEffects();
  }

  function renderNode(element, container, path) {
    if (element == null) {
      return;
    }
    if (Array.isArray(element)) {
      element.forEach((child, index) => renderNode(child, container, path + "." + index));
      return;
    }

    const { type, props } = element;
    if (type === TEXT_ELEMENT) {
      const text = document.createTextNode(props.nodeValue || "");
      container.appendChild(text);
      return;
    }

    if (type === Fragment) {
      const fragmentChildren = props.children || [];
      fragmentChildren.forEach((child, index) => renderNode(child, container, path + "." + index));
      return;
    }

    if (typeof type === "function") {
      const key = buildInstanceKey(path, type, props);
      let instance = instances.get(key);
      if (!instance || instance.type !== type) {
        if (instance) {
          cleanupInstance(instance);
        }
        instance = new ComponentInstance(type, key);
        instances.set(key, instance);
      }
      visitedInstances.add(key);
      const prevInstance = currentInstance;
      currentInstance = instance;
      instance.hookIndex = 0;
      instance.pendingEffects = [];
      const output = type(Object.assign({}, props));
      renderNode(output, container, key);
      queuedEffects.push({ key, instance, effects: instance.pendingEffects.slice() });
      currentInstance = prevInstance;
      return;
    }

    const dom = document.createElement(type);
    visitedInstances.add(path);
    applyProps(dom, {}, props || {});
    const children = props && props.children ? props.children : [];
    children.forEach((child, index) => renderNode(child, dom, path + ":" + index));
    container.appendChild(dom);
  }

  function applyProps(dom, prevProps, nextProps) {
    Object.keys(prevProps).forEach((name) => {
      if (name === "children") {
        return;
      }
      if (!(name in nextProps)) {
        setProp(dom, name, null);
      }
    });

    Object.keys(nextProps).forEach((name) => {
      if (name === "children") {
        return;
      }
      setProp(dom, name, nextProps[name]);
    });
  }

  function setProp(dom, name, value) {
    if (name === "style" && value && typeof value === "object") {
      Object.assign(dom.style, value);
      return;
    }
    if (name === "className") {
      dom.setAttribute("class", value || "");
      return;
    }
    if (name === "ref" && typeof value === "function") {
      value(dom);
      return;
    }
    if (name.startsWith("on") && typeof value === "function") {
      const eventName = name.slice(2).toLowerCase();
      dom.addEventListener(eventName, value);
      return;
    }
    if (value === false || value === null || value === undefined) {
      dom.removeAttribute(name);
      return;
    }
    dom.setAttribute(name, value === true ? "" : value);
  }

  function buildInstanceKey(path, type, props) {
    const name = type.displayName || type.name || "component";
    const key = props && props.key ? String(props.key) : "";
    return `${path}:${name}:${key}`;
  }

  function cleanupUnusedInstances() {
    const unused = [];
    instances.forEach((instance, key) => {
      if (!visitedInstances.has(key)) {
        unused.push(key);
        cleanupInstance(instance);
      }
    });
    unused.forEach((key) => instances.delete(key));
  }

  function cleanupInstance(instance) {
    instance.hooks.forEach((hook) => {
      if (hook && hook.kind === "effect" && typeof hook.cleanup === "function") {
        try {
          hook.cleanup();
        } catch (err) {
          console.warn("Error during effect cleanup", err);
        }
        hook.cleanup = undefined;
      }
    });
  }

  function runQueuedEffects() {
    queuedEffects.forEach(({ instance, effects }) => {
      effects.forEach((entry) => {
        const hook = instance.hooks[entry.index];
        if (!hook || hook.kind !== "effect") {
          return;
        }
        const deps = hook.nextDeps;
        const changed = depsChanged(hook.prevDeps, deps);
        if (!changed) {
          return;
        }
        if (typeof hook.cleanup === "function") {
          try {
            hook.cleanup();
          } catch (err) {
            console.warn("Error during effect cleanup", err);
          }
        }
        try {
          const cleanup = hook.effect();
          hook.cleanup = typeof cleanup === "function" ? cleanup : undefined;
          hook.prevDeps = deps ? deps.slice() : deps;
        } catch (err) {
          console.error("Effect execution error", err);
        }
      });
    });
  }

  function depsChanged(prev, next) {
    if (!prev || !next) {
      return true;
    }
    if (prev.length !== next.length) {
      return true;
    }
    for (let i = 0; i < prev.length; i += 1) {
      if (!Object.is(prev[i], next[i])) {
        return true;
      }
    }
    return false;
  }

  function prepareHook(kind) {
    if (!currentInstance) {
      throw new Error("Hooks can only be used inside function components");
    }
    const index = currentInstance.hookIndex++;
    let hook = currentInstance.hooks[index];
    if (!hook || hook.kind !== kind) {
      hook = { kind };
      currentInstance.hooks[index] = hook;
    }
    hook.index = index;
    return hook;
  }

  function useState(initialValue) {
    const hook = prepareHook("state");
    if (!Object.prototype.hasOwnProperty.call(hook, "value")) {
      hook.value = typeof initialValue === "function" ? initialValue() : initialValue;
    }
    const setState = (next) => {
      const value = typeof next === "function" ? next(hook.value) : next;
      if (!Object.is(value, hook.value)) {
        hook.value = value;
        scheduleRender();
      }
    };
    return [hook.value, setState];
  }

  function useReducer(reducer, initialArg, init) {
    const [state, setState] = useState(() => (init ? init(initialArg) : initialArg));
    const dispatch = (action) => {
      setState((prev) => reducer(prev, action));
    };
    return [state, dispatch];
  }

  function useMemo(factory, deps) {
    const hook = prepareHook("memo");
    if (!hook.hasOwnProperty("value") || depsChanged(hook.deps, deps)) {
      hook.value = factory();
      hook.deps = deps ? deps.slice() : deps;
    }
    return hook.value;
  }

  function useCallback(callback, deps) {
    return useMemo(() => callback, deps);
  }

  function useRef(initialValue) {
    const hook = prepareHook("ref");
    if (!hook.hasOwnProperty("current")) {
      hook.current = { current: initialValue };
    }
    return hook.current;
  }

  function useEffect(effect, deps) {
    const hook = prepareHook("effect");
    hook.effect = effect;
    hook.nextDeps = deps ? deps.slice() : deps;
    currentInstance.pendingEffects.push({ index: hook.index });
  }

  const MiniReact = {
    createElement,
    Fragment,
    render,
    useState,
    useReducer,
    useMemo,
    useCallback,
    useEffect,
    useRef,
    h: createElement
  };

  global.MiniReact = MiniReact;
})(window);
