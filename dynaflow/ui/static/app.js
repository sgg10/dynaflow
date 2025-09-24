(() => {
  const {
    h,
    Fragment,
    render,
    useState,
    useEffect,
    useMemo,
    useReducer,
    useCallback,
    useRef
  } = MiniReact;

  const NODE_TYPES = [
    { id: "Task", label: "Task", description: "Execute a registered function" },
    { id: "Pass", label: "Pass", description: "Inject or transform data" },
    { id: "Choice", label: "Choice", description: "Branch logic based on data" },
    { id: "Wait", label: "Wait", description: "Pause execution for a period" },
    { id: "Parallel", label: "Parallel", description: "Run branches concurrently" },
    { id: "Map", label: "Map", description: "Iterate over a collection" },
    { id: "Succeed", label: "Succeed", description: "Mark flow as successful" },
    { id: "Fail", label: "Fail", description: "Terminate execution with error" }
  ];

  const CHOICE_OPERATORS = [
    "BooleanEquals",
    "IsBoolean",
    "IsElementPresent",
    "IsNull",
    "IsNumeric",
    "IsString",
    "IsTimestamp",
    "NumericEquals",
    "NumericGreaterThan",
    "NumericGreaterThanEquals",
    "NumericLessThan",
    "NumericLessThanEquals",
    "StringEquals",
    "StringGreaterThan",
    "StringGreaterThanEquals",
    "StringLessThan",
    "StringLessThanEquals",
    "StringMatches",
    "TimestampEquals",
    "TimestampGreaterThan",
    "TimestampGreaterThanEquals",
    "TimestampLessThan",
    "TimestampLessThanEquals"
  ];

  const WAIT_MODES = [
    { id: "seconds", label: "Wait Seconds" },
    { id: "timestamp", label: "Wait Until Timestamp" },
    { id: "secondsPath", label: "Seconds Path" },
    { id: "timestampPath", label: "Timestamp Path" }
  ];

  const DEFAULT_NODE_WIDTH = 220;
  const DEFAULT_NODE_HEIGHT = 110;

  const NODE_NAME_PREFIX = {
    Task: "Task",
    Pass: "Pass",
    Choice: "Choice",
    Wait: "Wait",
    Map: "Map",
    Parallel: "Parallel",
    Succeed: "Success",
    Fail: "Fail"
  };

  function createInitialState() {
    const rootFlow = createFlow("root", "Root Flow", null);
    return {
      flows: { root: rootFlow },
      currentFlowId: "root",
      selection: null,
      catalogs: { items: [], aggregated: [], supportsRegistry: false },
      showInstallModal: false,
      validation: { status: "idle", errors: [] },
      toasts: [],
      revision: 0
    };
  }

  function createFlow(id, label, parent) {
    return {
      id,
      label,
      comment: "",
      version: "",
      startNodeId: null,
      nodes: {},
      order: [],
      parent
    };
  }

  function cloneValue(value) {
    if (value == null || typeof value !== "object") {
      return value;
    }
    if (Array.isArray(value)) {
      return value.map((item) => cloneValue(item));
    }
    const result = {};
    Object.keys(value).forEach((key) => {
      result[key] = cloneValue(value[key]);
    });
    return result;
  }

  function cloneNode(node) {
    return {
      ...node,
      position: { ...node.position },
      transitions: { ...node.transitions },
      config: cloneValue(node.config),
      branchFlowIds: node.branchFlowIds ? node.branchFlowIds.slice() : []
    };
  }

  function cloneFlow(flow) {
    const nodes = {};
    Object.keys(flow.nodes).forEach((id) => {
      nodes[id] = cloneNode(flow.nodes[id]);
    });
    return {
      ...flow,
      nodes,
      order: flow.order.slice()
    };
  }

  function createId(prefix = "node") {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return `${prefix}-${Math.random().toString(16).slice(2)}`;
  }

  function ensureUniqueName(flow, baseName, excludeId) {
    let counter = 1;
    let candidate = baseName;
    const taken = new Set(
      flow.order
        .filter((id) => id !== excludeId)
        .map((id) => flow.nodes[id].name.toLowerCase())
    );
    while (taken.has(candidate.toLowerCase())) {
      counter += 1;
      candidate = `${baseName} ${counter}`;
    }
    return candidate;
  }

  function createTaskConfig() {
    return {
      functionFields: [
        { id: createId("fn"), key: "Name", value: "", required: true }
      ],
      parameters: [],
      inputPath: "",
      outputPath: "",
      resultPath: "",
      heartbeatSeconds: "",
      timeoutSeconds: "",
      retry: [],
      catch: []
    };
  }

  function createPassConfig() {
    return {
      result: "",
      resultIsJson: false,
      parameters: [],
      inputPath: "",
      outputPath: "",
      resultPath: ""
    };
  }

  function createChoiceConfig() {
    return {
      choices: [
        {
          id: createId("choice"),
          variable: "",
          operator: "StringEquals",
          value: "",
          next: null
        }
      ],
      default: null
    };
  }

  function createWaitConfig() {
    return {
      mode: "seconds",
      seconds: "",
      timestamp: "",
      secondsPath: "",
      timestampPath: "",
      inputPath: "",
      outputPath: "",
      resultPath: ""
    };
  }

  function createMapConfig(name) {
    return {
      itemsPath: "$.items",
      parameters: [],
      resultPath: "",
      maxConcurrency: "",
      iteratorLabel: `${name} Iterator`
    };
  }

  function createParallelConfig(name) {
    return {
      branchLabelPrefix: `${name} Branch`
    };
  }

  function createFailConfig() {
    return {
      error: "",
      cause: ""
    };
  }

  function createSucceedConfig() {
    return {};
  }

  function createNodeTemplate(type, flow, options) {
    const id = createId(type.toLowerCase());
    const baseName = NODE_NAME_PREFIX[type] || type;
    const name = ensureUniqueName(flow, baseName, null);
    const position = options && options.position ? options.position : { x: 120, y: 120 };
    const baseNode = {
      id,
      flowId: flow.id,
      name,
      type,
      comment: "",
      position,
      transitions: { next: null, end: false, default: null },
      config: {},
      branchFlowIds: []
    };

    const newFlows = [];

    if (type === "Task") {
      baseNode.config = createTaskConfig();
    } else if (type === "Pass") {
      baseNode.config = createPassConfig();
    } else if (type === "Choice") {
      baseNode.config = createChoiceConfig();
    } else if (type === "Wait") {
      baseNode.config = createWaitConfig();
    } else if (type === "Map") {
      baseNode.config = createMapConfig(name);
      const branchId = `${id}:iterator`;
      baseNode.branchFlowIds.push(branchId);
      newFlows.push(
        createFlow(branchId, `${name} Iterator`, {
          flowId: flow.id,
          nodeId: id,
          type: "Map",
          label: `${name} Iterator`
        })
      );
    } else if (type === "Parallel") {
      baseNode.config = createParallelConfig(name);
      const branchId = `${id}:branch-1`;
      baseNode.branchFlowIds.push(branchId);
      newFlows.push(
        createFlow(branchId, `${name} Branch 1`, {
          flowId: flow.id,
          nodeId: id,
          type: "Parallel",
          label: `${name} Branch 1`
        })
      );
    } else if (type === "Fail") {
      baseNode.config = createFailConfig();
      baseNode.transitions.end = true;
    } else if (type === "Succeed") {
      baseNode.config = createSucceedConfig();
      baseNode.transitions.end = true;
    }

    return { node: baseNode, flows: newFlows };
  }

  function produce(state, mutator, options) {
    const next = {
      ...state,
      flows: { ...state.flows },
      catalogs: { ...state.catalogs },
      validation: { ...state.validation },
      toasts: state.toasts.slice()
    };
    mutator(next);
    if (!options || options.increment !== false) {
      next.revision = (state.revision || 0) + 1;
    }
    return next;
  }

  function reducer(state, action) {
    switch (action.type) {
      case "SET_CATALOGS":
        return {
          ...state,
          catalogs: {
            items: action.payload.items,
            aggregated: action.payload.aggregated,
            supportsRegistry: action.payload.supportsRegistry
          }
        };
      case "TOGGLE_INSTALL_MODAL":
        return { ...state, showInstallModal: action.visible };
      case "SET_SELECTION":
        console.log('🎯 SET_SELECTION action:', action.selection);
        return { ...state, selection: action.selection };
      case "CLEAR_SELECTION":
        return { ...state, selection: null };
      case "NAVIGATE_FLOW":
        return { ...state, currentFlowId: action.flowId, selection: null };
      case "ADD_TOAST":
        return { ...state, toasts: [...state.toasts, action.toast] };
      case "REMOVE_TOAST":
        return {
          ...state,
          toasts: state.toasts.filter((toast) => toast.id !== action.id)
        };
      case "SET_VALIDATION":
        return {
          ...state,
          validation: { status: action.status, errors: action.errors || [] }
        };
      case "ADD_NODE": {
        console.log('🔧 ADD_NODE action:', action);
        const flow = state.flows[action.flowId];
        if (!flow) {
          console.error('Flow no encontrado:', action.flowId);
          return state;
        }
        return produce(state, (draft) => {
          const baseFlow = cloneFlow(flow);
          const { node, flows: newFlows } = createNodeTemplate(action.nodeType, baseFlow, {
            position: action.position
          });
          console.log('✅ Nodo creado:', node);
          
          // Auto-conectar al nodo anterior si existe
          const lastNodeId = baseFlow.order[baseFlow.order.length - 1];
          if (lastNodeId && baseFlow.nodes[lastNodeId]) {
            const lastNode = baseFlow.nodes[lastNodeId];
            if (!lastNode.transitions.next && !lastNode.transitions.end) {
              console.log('🔗 Conectando automáticamente:', lastNodeId, '->', node.id);
              lastNode.transitions.next = node.id;
            }
          }
          
          baseFlow.nodes[node.id] = node;
          baseFlow.order.push(node.id);
          if (!baseFlow.startNodeId) {
            baseFlow.startNodeId = node.id;
          }
          draft.flows[action.flowId] = baseFlow;
          newFlows.forEach((branchFlow) => {
            draft.flows[branchFlow.id] = branchFlow;
          });
          draft.selection = { flowId: action.flowId, nodeId: node.id };
        });
      }
      case "UPDATE_NODE_POSITION": {
        console.log('🔄 UPDATE_NODE_POSITION action:', action);
        const flow = state.flows[action.flowId];
        if (!flow || !flow.nodes[action.nodeId]) {
          console.error('Flow o nodo no encontrado:', { flowId: action.flowId, nodeId: action.nodeId });
          return state;
        }
        const node = flow.nodes[action.nodeId];
        if (
          node.position.x === action.position.x &&
          node.position.y === action.position.y
        ) {
          console.log('Posición igual, no hay cambios');
          return state;
        }
        console.log('✅ Actualizando posición del nodo:', { from: node.position, to: action.position });
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          const updatedNode = cloneNode(updatedFlow.nodes[action.nodeId]);
          updatedNode.position = { ...action.position };
          updatedFlow.nodes[action.nodeId] = updatedNode;
          draft.flows[action.flowId] = updatedFlow;
        });
      }
      case "UPDATE_NODE": {
        const flow = state.flows[action.flowId];
        if (!flow || !flow.nodes[action.nodeId]) {
          return state;
        }
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          const node = cloneNode(updatedFlow.nodes[action.nodeId]);
          if (action.changes.name) {
            node.name = ensureUniqueName(updatedFlow, action.changes.name, node.id);
          }
          if (action.changes.comment !== undefined) {
            node.comment = action.changes.comment;
          }
          if (action.changes.transitions) {
            console.log('🔗 Actualizando transiciones:', action.changes.transitions);
            node.transitions = { ...node.transitions, ...action.changes.transitions };
          }
          if (action.changes.config) {
            node.config = cloneValue(action.changes.config);
          }
          updatedFlow.nodes[action.nodeId] = node;
          draft.flows[action.flowId] = updatedFlow;
          if (action.changes.start === true) {
            updatedFlow.startNodeId = node.id;
          }
          // Incrementar revision para forzar re-render de conexiones
          draft.revision = (state.revision || 0) + 1;
          
          // Actualizar selection si es el nodo actual para refrescar ConfigPanel
          if (state.selection && state.selection.nodeId === action.nodeId) {
            draft.selection = { ...state.selection, nodeId: action.nodeId };
          }
        });
      }
      case "UPDATE_NODE_CONFIG": {
        const flow = state.flows[action.flowId];
        if (!flow || !flow.nodes[action.nodeId]) {
          return state;
        }
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          const node = cloneNode(updatedFlow.nodes[action.nodeId]);
          const nextConfig = cloneValue(node.config);
          action.updater(nextConfig);
          node.config = nextConfig;
          updatedFlow.nodes[action.nodeId] = node;
          draft.flows[action.flowId] = updatedFlow;
        });
      }
      case "SET_FLOW_START": {
        const flow = state.flows[action.flowId];
        if (!flow || !flow.nodes[action.nodeId]) {
          return state;
        }
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          updatedFlow.startNodeId = action.nodeId;
          draft.flows[action.flowId] = updatedFlow;
        });
      }
      case "REMOVE_NODE": {
        const flow = state.flows[action.flowId];
        if (!flow || !flow.nodes[action.nodeId]) {
          return state;
        }
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          const node = updatedFlow.nodes[action.nodeId];
          delete updatedFlow.nodes[action.nodeId];
          updatedFlow.order = updatedFlow.order.filter((id) => id !== action.nodeId);
          if (updatedFlow.startNodeId === action.nodeId) {
            updatedFlow.startNodeId = updatedFlow.order[0] || null;
          }
          updatedFlow.order.forEach((id) => {
            const current = updatedFlow.nodes[id];
            if (current.transitions.next === action.nodeId) {
              current.transitions.next = null;
            }
            if (current.transitions.default === action.nodeId) {
              current.transitions.default = null;
            }
            if (current.type === "Choice") {
              current.config.choices = current.config.choices.map((choice) =>
                choice.next === action.nodeId ? { ...choice, next: null } : choice
              );
            }
          });
          if (node.branchFlowIds && node.branchFlowIds.length) {
            node.branchFlowIds.forEach((flowId) => {
              removeFlowBranch(draft, flowId);
            });
          }
          draft.flows[action.flowId] = updatedFlow;
          draft.selection = null;
        });
      }
      case "ADD_PARALLEL_BRANCH": {
        const flow = state.flows[action.flowId];
        if (!flow) return state;
        const node = flow.nodes[action.nodeId];
        if (!node || node.type !== "Parallel") return state;
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          const updatedNode = cloneNode(updatedFlow.nodes[action.nodeId]);
          const branchIndex = updatedNode.branchFlowIds.length + 1;
          const branchId = `${updatedNode.id}:branch-${branchIndex}`;
          updatedNode.branchFlowIds.push(branchId);
          updatedFlow.nodes[action.nodeId] = updatedNode;
          draft.flows[action.flowId] = updatedFlow;
          const labelPrefix = updatedNode.config.branchLabelPrefix || `${updatedNode.name} Branch`;
          draft.flows[branchId] = createFlow(branchId, `${labelPrefix} ${branchIndex}`, {
            flowId: flow.id,
            nodeId: action.nodeId,
            type: "Parallel",
            label: `${labelPrefix} ${branchIndex}`
          });
        });
      }
      case "REMOVE_PARALLEL_BRANCH": {
        const flow = state.flows[action.flowId];
        if (!flow) return state;
        const node = flow.nodes[action.nodeId];
        if (!node || node.type !== "Parallel") return state;
        if (node.branchFlowIds.length <= 1) return state;
        return produce(state, (draft) => {
          const updatedFlow = cloneFlow(flow);
          const updatedNode = cloneNode(updatedFlow.nodes[action.nodeId]);
          const [removed] = updatedNode.branchFlowIds.splice(action.index, 1);
          updatedFlow.nodes[action.nodeId] = updatedNode;
          draft.flows[action.flowId] = updatedFlow;
          if (removed) {
            removeFlowBranch(draft, removed);
          }
        });
      }
      case "UPDATE_FLOW": {
        const flow = state.flows[action.flowId];
        if (!flow) return state;
        return produce(state, (draft) => {
          draft.flows[action.flowId] = { ...flow, ...action.changes };
        });
      }
      default:
        return state;
    }
  }

  function removeFlowBranch(state, flowId) {
    const branch = state.flows[flowId];
    if (!branch) {
      return;
    }
    Object.values(branch.nodes).forEach((node) => {
      if (node.branchFlowIds && node.branchFlowIds.length) {
        node.branchFlowIds.forEach((nested) => removeFlowBranch(state, nested));
      }
    });
    delete state.flows[flowId];
  }

  function formatToast(message, tone) {
    return {
      id: createId("toast"),
      message,
      tone,
      timestamp: Date.now()
    };
  }

  function buildFlowExport(state) {
    const rootFlow = state.flows["root"];
    return exportFlow(state, rootFlow);
  }

  function exportFlow(state, flow) {
    if (!flow) {
      return {};
    }
    const result = {};
    if (flow.comment) {
      result.Comment = flow.comment;
    }
    if (flow.version) {
      result.Version = flow.version;
    }
    if (flow.startNodeId && flow.nodes[flow.startNodeId]) {
      result.StartAt = flow.nodes[flow.startNodeId].name;
    }
    const states = {};
    flow.order.forEach((nodeId) => {
      const node = flow.nodes[nodeId];
      states[node.name] = exportNode(state, flow, node);
    });
    result.States = states;
    return result;
  }

  function exportNode(state, flow, node) {
    const base = { Type: node.type };
    if (node.comment) {
      base.Comment = node.comment;
    }
    if (node.transitions.end) {
      base.End = true;
    } else if (node.transitions.next && flow.nodes[node.transitions.next]) {
      base.Next = flow.nodes[node.transitions.next].name;
    }

    if (node.type === "Task") {
      Object.assign(base, exportTask(node));
    } else if (node.type === "Pass") {
      Object.assign(base, exportPass(node));
    } else if (node.type === "Choice") {
      Object.assign(base, exportChoice(flow, node));
    } else if (node.type === "Wait") {
      Object.assign(base, exportWait(node));
    } else if (node.type === "Map") {
      Object.assign(base, exportMap(state, node));
    } else if (node.type === "Parallel") {
      Object.assign(base, exportParallel(state, node));
    } else if (node.type === "Fail") {
      Object.assign(base, exportFail(node));
    } else if (node.type === "Succeed") {
      Object.assign(base, exportSucceed());
    }
    return base;
  }

  function exportTask(node) {
    const payload = {};
    const fn = {};
    (node.config.functionFields || []).forEach((field) => {
      if (!field.key) return;
      if (field.key === "Name" && !field.value) return;
      fn[field.key] = coerceValue(field.value);
    });
    if (Object.keys(fn).length) {
      payload.Function = fn;
    }
    if (node.config.inputPath) payload.InputPath = node.config.inputPath;
    if (node.config.outputPath) payload.OutputPath = node.config.outputPath;
    if (node.config.resultPath) payload.ResultPath = node.config.resultPath;
    if (node.config.heartbeatSeconds) payload.HeartbeatSeconds = Number(node.config.heartbeatSeconds);
    if (node.config.timeoutSeconds) payload.TimeoutSeconds = Number(node.config.timeoutSeconds);
    const params = exportParameters(node.config.parameters || []);
    if (params) payload.Parameters = params;
    return payload;
  }

  function exportPass(node) {
    const payload = {};
    if (node.config.result) {
      payload.Result = node.config.resultIsJson
        ? safeJsonParse(node.config.result)
        : coerceValue(node.config.result);
    }
    if (node.config.inputPath) payload.InputPath = node.config.inputPath;
    if (node.config.outputPath) payload.OutputPath = node.config.outputPath;
    if (node.config.resultPath) payload.ResultPath = node.config.resultPath;
    const params = exportParameters(node.config.parameters || []);
    if (params) payload.Parameters = params;
    return payload;
  }

  function exportChoice(flow, node) {
    const payload = { Choices: [] };
    (node.config.choices || []).forEach((choice) => {
      if (!choice.variable || !choice.operator) return;
      const rule = { Variable: choice.variable };
      rule[choice.operator] = coerceValue(choice.value);
      if (choice.next && flow.nodes[choice.next]) {
        rule.Next = flow.nodes[choice.next].name;
      }
      payload.Choices.push(rule);
    });
    if (node.transitions.default && flow.nodes[node.transitions.default]) {
      payload.Default = flow.nodes[node.transitions.default].name;
    }
    return payload;
  }

  function exportWait(node) {
    const payload = {};
    const mode = node.config.mode;
    if (mode === "seconds") {
      payload.Seconds = Number(node.config.seconds || 0);
    } else if (mode === "timestamp") {
      payload.Timestamp = node.config.timestamp;
    } else if (mode === "secondsPath") {
      payload.SecondsPath = node.config.secondsPath;
    } else if (mode === "timestampPath") {
      payload.TimestampPath = node.config.timestampPath;
    }
    if (node.config.inputPath) payload.InputPath = node.config.inputPath;
    if (node.config.outputPath) payload.OutputPath = node.config.outputPath;
    if (node.config.resultPath) payload.ResultPath = node.config.resultPath;
    return payload;
  }

  function exportMap(state, node) {
    const payload = { ItemsPath: node.config.itemsPath || "$.items" };
    const flowIds = node.branchFlowIds || [];
    if (flowIds[0] && state.flows[flowIds[0]]) {
      payload.ItemProcessor = exportFlow(state, state.flows[flowIds[0]]);
    }
    if (node.config.resultPath) payload.ResultPath = node.config.resultPath;
    if (node.config.maxConcurrency) payload.MaxConcurrency = Number(node.config.maxConcurrency);
    const params = exportParameters(node.config.parameters || []);
    if (params) payload.Parameters = params;
    return payload;
  }

  function exportParallel(state, node) {
    const branches = [];
    (node.branchFlowIds || []).forEach((flowId) => {
      const branch = state.flows[flowId];
      if (branch) {
        branches.push(exportFlow(state, branch));
      }
    });
    return { Branches: branches };
  }

  function exportFail(node) {
    const payload = {};
    if (node.config.error) payload.Error = node.config.error;
    if (node.config.cause) payload.Cause = node.config.cause;
    return payload;
  }

  function exportSucceed() {
    return {};
  }

  function exportParameters(parameters) {
    if (!parameters.length) {
      return null;
    }
    const result = {};
    parameters.forEach((param) => {
      if (!param.name) return;
      const key = param.mode === "path" ? ensureSuffix(param.name, ".$") : param.name;
      result[key] = param.mode === "path"
        ? param.value
        : safeJsonParse(param.value, param.value);
    });
    return result;
  }

  function ensureSuffix(value, suffix) {
    return value.endsWith(suffix) ? value : `${value}${suffix}`;
  }

  function safeJsonParse(value, fallback) {
    if (typeof value !== "string") {
      return value;
    }
    const trimmed = value.trim();
    if (!trimmed) {
      return fallback !== undefined ? fallback : trimmed;
    }
    if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
      try {
        return JSON.parse(trimmed);
      } catch (err) {
        return fallback !== undefined ? fallback : trimmed;
      }
    }
    if (trimmed === "true" || trimmed === "false") {
      return trimmed === "true";
    }
    if (!Number.isNaN(Number(trimmed))) {
      return Number(trimmed);
    }
    return fallback !== undefined ? fallback : trimmed;
  }

  function coerceValue(value) {
    if (value === "" || value === null || value === undefined) {
      return "";
    }
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (trimmed === "true" || trimmed === "false") {
        return trimmed === "true";
      }
      const number = Number(trimmed);
      if (!Number.isNaN(number) && trimmed !== "") {
        return number;
      }
      return value;
    }
    return value;
  }

  function useToasts(state, dispatch) {
    useEffect(() => {
      if (!state.toasts.length) {
        return;
      }
      const timers = state.toasts.map((toast) =>
        setTimeout(() => {
          dispatch({ type: "REMOVE_TOAST", id: toast.id });
        }, 4200)
      );
      return () => timers.forEach((timer) => clearTimeout(timer));
    }, [state.toasts]);
  }

  function useCatalogs(dispatch) {
    useEffect(() => {
      fetchCatalogs(dispatch);
    }, []); // Solo ejecutar una vez al montar el componente
  }

  function fetchCatalogs(dispatch) {
    fetch("/api/catalogs")
      .then((response) => response.json())
      .then((payload) => {
        dispatch({
          type: "SET_CATALOGS",
          payload: {
            items: payload.catalogs || [],
            aggregated: payload.functions || [],
            supportsRegistry: Boolean(payload.supports_registry)
          }
        });
      })
      .catch(() => {
        dispatch({
          type: "ADD_TOAST",
          toast: formatToast("Unable to load catalogs", "error")
        });
      });
  }

  function computeEdges(flow) {
    if (!flow) return [];
    const edges = [];
    console.log('🔗 Computando edges para flow:', flow.id, 'con nodos:', Object.keys(flow.nodes));
    
    flow.order.forEach((nodeId) => {
      const node = flow.nodes[nodeId];
      if (!node) return;
      if (node.transitions.next) {
        console.log('➡️ Creando edge:', nodeId, '->', node.transitions.next);
        edges.push({
          id: `next-${nodeId}`,
          from: nodeId,
          to: node.transitions.next,
          label: node.type === "Choice" ? "" : "Next"
        });
      }
      if (node.type === "Choice") {
        (node.config.choices || []).forEach((choice, index) => {
          if (choice.next) {
            console.log('🔀 Creando choice edge:', nodeId, '->', choice.next);
            edges.push({
              id: `choice-${nodeId}-${index}`,
              from: nodeId,
              to: choice.next,
              label: choice.operator || `Rule ${index + 1}`
            });
          }
        });
        if (node.transitions.default) {
          console.log('🔄 Creando default edge:', nodeId, '->', node.transitions.default);
          edges.push({
            id: `choice-default-${nodeId}`,
            from: nodeId,
            to: node.transitions.default,
            label: "Default"
          });
        }
      }
    });
    
    console.log('🔗 Total edges creados:', edges.length, edges);
    return edges;
  }

  function getNodeClass(type) {
    return `node-card node-${type.toLowerCase()}`;
  }

  function ToastContainer({ toasts }) {
    if (!toasts.length) return null;
    return h(
      'div',
      { className: 'toast-container' },
      toasts.map((toast) =>
        h(
          'div',
          { className: `toast ${toast.tone || 'info'}`, key: toast.id },
          toast.message
        )
      )
    );
  }

  function AppHeader({ flow, flows, onDownload, onValidate, onOpenInstall, onNavigateFlow, validation }) {
    // Construir breadcrumb desde el flow actual hacia arriba
    const buildBreadcrumb = () => {
      if (!flow) return [];
      
      const breadcrumb = [];
      let currentFlow = flow;
      
      while (currentFlow) {
        breadcrumb.unshift(currentFlow);
        
        if (currentFlow.parent && flows[currentFlow.parent.flowId]) {
          currentFlow = flows[currentFlow.parent.flowId];
        } else {
          break;
        }
      }
      
      return breadcrumb;
    };
    
    const breadcrumb = buildBreadcrumb();
    
    return h('header', { className: 'app-header' }, [
      h('div', { className: 'title-block' }, [
        h('h1', { className: 'title' }, 'DynaFlow Studio'),
        breadcrumb.length > 1 ? h('div', { className: 'breadcrumb' }, 
          breadcrumb.map((breadFlow, index) => 
            h('span', { key: breadFlow.id, className: 'breadcrumb-item' }, [
              index > 0 ? h('span', { className: 'breadcrumb-separator' }, ' / ') : null,
              h('button', {
                className: breadFlow.id === flow.id ? 'breadcrumb-current' : 'breadcrumb-link',
                onClick: () => breadFlow.id !== flow.id && onNavigateFlow(breadFlow.id)
              }, breadFlow.label)
            ])
          )
        ) : h('span', { className: 'tagline' }, flow ? flow.label : 'Workflow')
      ]),
      h('div', { className: 'header-actions' }, [
        h(
          'button',
          {
            onClick: onOpenInstall
          },
          'Install catalog'
        ),
        h(
          'button',
          {
            onClick: onValidate
          },
          validation.status === 'running' ? 'Validating…' : 'Validate flow'
        ),
        h(
          'button',
          {
            className: 'primary',
            onClick: onDownload
          },
          'Download JSON'
        ),
        h(
          'button',
          {
            onClick: () => {
              console.log('🧪 DEBUG STATE:', window.debugState);
              console.log('🧪 CURRENT FLOW:', window.debugState?.flows[window.debugState?.currentFlowId]);
            }
          },
          'Debug State'
        ),
        h(
          'button',
          {
            onClick: () => {
              const currentFlow = window.debugState?.flows[window.debugState?.currentFlowId];
              if (currentFlow && currentFlow.order.length >= 2) {
                const firstNode = currentFlow.order[0];
                const secondNode = currentFlow.order[1];
                console.log('🧪 TEST: Conectando manualmente', firstNode, '->', secondNode);
                window.debugDispatch({
                  type: 'UPDATE_NODE',
                  flowId: currentFlow.id,
                  nodeId: firstNode,
                  changes: { transitions: { next: secondNode } }
                });
              }
            }
          },
          'Test Connect'
        )
      ])
    ]);
  }

  function Sidebar({ catalogs, onRefreshCatalog, onRemoveCatalog, onAddNode }) {
    return h('aside', { className: 'sidebar' }, [
      h('div', { className: 'section-header' }, 'Function catalogs'),
      h('div', { className: 'sidebar-content' }, [
        h(CatalogList, {
          catalogs,
          onRefresh: onRefreshCatalog,
          onRemove: onRemoveCatalog
        }),
        h('div', { className: 'palette' }, [
          h('div', { className: 'section-header' }, 'Node palette'),
          h('small', { className: 'subtitle', style: { marginBottom: '8px', display: 'block' } }, 'Haz clic en el botón + para agregar nodos'),
          h(NodePalette, { onAddNode })
        ])
      ])
    ]);
  }

  function CatalogList({ catalogs, onRefresh, onRemove }) {
    if (!catalogs.length) {
      return h('div', { className: 'empty-state' }, 'No catalogs registered yet. Install one to bootstrap your tasks.');
    }
    return h(
      Fragment,
      null,
      catalogs.map((catalog) =>
        h('div', { className: 'catalog-card', key: catalog.alias }, [
          h('div', { className: 'catalog-header' }, [
            h('strong', null, catalog.alias || catalog.module),
            catalog.module ? h('div', { className: 'meta' }, catalog.module) : null
          ]),
          catalog.metadata && catalog.metadata.source
            ? h('div', { className: 'meta' }, catalog.metadata.source)
            : null,
          catalog.error ? h('div', { className: 'error' }, catalog.error) : null,
          h('div', { className: 'catalog-actions' }, [
            h(
              'button',
              {
                onClick: () => onRefresh && onRefresh(catalog.alias)
              },
              'Refresh'
            ),
            h(
              'button',
              {
                onClick: () => onRemove && onRemove(catalog.alias)
              },
              'Remove'
            )
          ])
        ])
      )
    );
  }

  function NodePalette({ onAddNode }) {
    return h(
      'div',
      null,
      NODE_TYPES.map((node) =>
          h(
            'div',
            {
              className: 'node-type',
              key: node.id,
              draggable: true,
              onClick: (event) => {
                console.log('🔍 Click simple en nodo:', node.id);
                if (event.detail === 2) { // Detectar doble clic
                  console.log('📋 DOBLE CLIC detectado en nodo de paleta:', node.id);
                  console.log('onAddNode disponible:', !!onAddNode);
                  if (onAddNode) {
                    // Agregar en una posición centrada y un poco aleatoria
                    const position = {
                      x: 200 + Math.random() * 300,
                      y: 150 + Math.random() * 200
                    };
                    console.log('Agregando nodo en posición:', position);
                    onAddNode(node.id, position);
                  } else {
                    console.error('onAddNode no está disponible');
                  }
                }
              },
              onDragStart: (event) => {
                event.dataTransfer.effectAllowed = 'copy';
                event.dataTransfer.setData('application/x-node-type', node.id);
              }
            },
          [
            h('div', { className: 'node-info' }, [
              h('span', null, node.label),
              h('small', { className: 'subtitle' }, node.description)
            ]),
            h('button', {
              className: 'add-node-btn',
              onClick: (event) => {
                event.stopPropagation();
                console.log('➕ Botón + presionado para nodo:', node.id);
                if (onAddNode) {
                  const position = {
                    x: 200 + Math.random() * 300,
                    y: 150 + Math.random() * 200
                  };
                  console.log('Agregando nodo desde botón en posición:', position);
                  onAddNode(node.id, position);
                } else {
                  console.error('onAddNode no está disponible desde botón');
                }
              }
            }, '+')
          ]
        )
      )
    );
  }

  function CanvasView({
    flow,
    selection,
    canvasRef,
    edges,
    nodeRects,
    onDropNode,
    onSelectNode,
    onMoveNode,
    onOpenFlow,
    onMeasureNode,
    pan,
    onPanChange
  }) {
    const panStateRef = useRef(pan);
    const dragStartRef = useRef({ x: 0, y: 0 });
    const pointerStartRef = useRef({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);

    useEffect(() => {
      panStateRef.current = pan;
    }, [pan]);

    const attachCanvasRef = useCallback(
      (element) => {
        if (canvasRef) {
          canvasRef.current = element;
        }
      },
      [canvasRef]
    );

    const handleDrop = (event) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData('application/x-node-type');
      if (!nodeType || !flow || !canvasRef || !canvasRef.current) return;
      const rect = canvasRef.current.getBoundingClientRect();
      const position = {
        x: event.clientX - rect.left - pan.x - 100,
        y: event.clientY - rect.top - pan.y - 40
      };
      onDropNode(nodeType, position);
    };

    const handleDragOver = (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
    };

    const handleBackgroundMouseDown = useCallback(
      (event) => {
        if (!canvasRef || !canvasRef.current) return;
        if (event.button !== 0) return;
        if (event.target !== canvasRef.current) return;

        event.preventDefault();
        pointerStartRef.current = { x: event.clientX, y: event.clientY };
        dragStartRef.current = { ...panStateRef.current };
        setIsPanning(true);
        document.body.style.cursor = 'grabbing';

        const handleMouseMove = (moveEvent) => {
          const dx = moveEvent.clientX - pointerStartRef.current.x;
          const dy = moveEvent.clientY - pointerStartRef.current.y;
          onPanChange({
            x: dragStartRef.current.x + dx,
            y: dragStartRef.current.y + dy
          });
        };

        const handleMouseUp = () => {
          document.removeEventListener('mousemove', handleMouseMove);
          document.removeEventListener('mouseup', handleMouseUp);
          document.body.style.cursor = '';
          setIsPanning(false);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
      },
      [canvasRef, onPanChange]
    );

    const handleWheel = useCallback(
      (event) => {
        if (event.ctrlKey) {
          return;
        }
        event.preventDefault();
        const nextPan = {
          x: panStateRef.current.x - event.deltaX,
          y: panStateRef.current.y - event.deltaY
        };
        onPanChange(nextPan);
      },
      [onPanChange]
    );

    return h(
      'div',
      {
        className: 'canvas',
        onDrop: handleDrop,
        onDragOver: handleDragOver,
        onWheel: handleWheel
      },
      [
        h(LinkLayer, { edges, rects: nodeRects, nodes: flow ? flow.nodes : {}, pan }),
        h(
          'div',
          {
            className: `canvas-inner${isPanning ? ' is-panning' : ''}`,
            ref: attachCanvasRef,
            onMouseDown: handleBackgroundMouseDown,
            style: {
              transform: `translate(${pan.x}px, ${pan.y}px)`
            }
          },
        flow && flow.order.length
          ? flow.order.map((nodeId) => {
              const node = flow.nodes[nodeId];
              return h(NodeCard, {
                key: node.id,
                node,
                selected: selection && selection.nodeId === node.id,
                onSelect: onSelectNode,
                onMove: onMoveNode,
                onOpenFlow,
                onMeasure: onMeasureNode,
                isStart: flow.startNodeId === node.id,
                isEnd: Boolean(node.transitions.end)
              });
            })
          : h('div', { className: 'empty-state' }, 'Drag a node from the palette to begin designing your flow.')
      )
    ]);
  }

  function NodeCard({
    node,
    selected,
    onSelect,
    onMove,
    onOpenFlow,
    onMeasure,
    isStart,
    isEnd
  }) {
    const ref = useRef(null);

    const handleDoubleClick = useCallback(() => {
      if ((node.type === 'Map' || node.type === 'Parallel') && node.branchFlowIds.length) {
        onOpenFlow(node.branchFlowIds[0]);
      }
    }, [node, onOpenFlow]);

    // Manejadores simples como propiedades del elemento
    const handleClick = useCallback((event) => {
      event.stopPropagation();
      console.log('🖱️ CLICK SIMPLE en nodo:', node.id);
      onSelect(node.id);
    }, [node.id, onSelect]);

    const handleMouseDown = useCallback((event) => {
      if (event.button !== 0) return;

      console.log('🖱️ MOUSEDOWN en nodo:', node.id);
      event.preventDefault();
      
      let isDragging = false;
      const startX = event.clientX;
      const startY = event.clientY;
      const initialPosition = { ...node.position };
      
      const handleMouseMove = (moveEvent) => {
        const deltaX = Math.abs(moveEvent.clientX - startX);
        const deltaY = Math.abs(moveEvent.clientY - startY);
        
        if (!isDragging && (deltaX > 5 || deltaY > 5)) {
          isDragging = true;
          console.log('🚀 INICIANDO ARRASTRE del nodo:', node.id);
          document.body.style.cursor = 'grabbing';
        }
        
        if (isDragging) {
          const dx = moveEvent.clientX - startX;
          const dy = moveEvent.clientY - startY;
          const newPosition = {
            x: initialPosition.x + dx,
            y: initialPosition.y + dy
          };
          console.log('📍 MOVIENDO nodo:', node.id, 'a posición:', newPosition);
          onMove(node.id, newPosition);
        }
      };
      
      const handleMouseUp = () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
        
        if (isDragging) {
          console.log('🛑 FIN ARRASTRE del nodo:', node.id);
        }
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }, [node.id, node.position, onMove]);

    useEffect(() => {
      if (!ref.current || !onMeasure) {
        return;
      }

      const element = ref.current;
      let frame = null;

      const updateRect = () => {
        if (!element) {
          return;
        }
        onMeasure(node.id, {
          left: node.position.x,
          top: node.position.y,
          width: element.offsetWidth,
          height: element.offsetHeight
        });
      };

      frame = requestAnimationFrame(updateRect);

      let resizeObserver = null;
      if (typeof ResizeObserver === 'function') {
        resizeObserver = new ResizeObserver(() => {
          if (frame) {
            cancelAnimationFrame(frame);
          }
          frame = requestAnimationFrame(updateRect);
        });
        resizeObserver.observe(element);
      }

      return () => {
        if (frame) {
          cancelAnimationFrame(frame);
        }
        if (resizeObserver) {
          resizeObserver.disconnect();
        }
      };
    }, [
      node.id,
      node.position.x,
      node.position.y,
      node.name,
      node.comment,
      node.type,
      node.transitions.end,
      node.branchFlowIds && node.branchFlowIds.length,
      onMeasure
    ]);

    useEffect(() => {
      if (!onMeasure) {
        return () => {};
      }
      const nodeId = node.id;
      return () => {
        onMeasure(nodeId, null);
      };
    }, [node.id, onMeasure]);

    const className = `${getNodeClass(node.type)}${selected ? ' selected' : ''}`;

    return h(
      'div',
      {
        className,
        ref,
        'data-node-id': node.id,
        style: {
          left: `${node.position.x}px`,
          top: `${node.position.y}px`
        },
        onClick: handleClick,
        onMouseDown: handleMouseDown,
        onDoubleClick: handleDoubleClick
      },
      [
        isStart ? h('span', { className: 'node-marker node-marker-start', title: 'Start state' }) : null,
        isEnd ? h('span', { className: 'node-marker node-marker-end', title: 'End state' }) : null,
        h('div', { className: 'title' }, [
          h('strong', null, node.name),
          h('span', { className: 'tag' }, node.type)
        ]),
        node.comment ? h('div', { className: 'subtitle' }, node.comment) : null,
        (node.type === 'Map' || node.type === 'Parallel') && node.branchFlowIds.length
          ? h(
              'button',
              {
                className: 'open-branch',
                onClick: () => onOpenFlow(node.branchFlowIds[0])
              },
              'Open'
            )
          : null
      ]
    );
  }

  function LinkLayer({ edges, rects, nodes, pan }) {
    if (!edges.length) {
      return null;
    }

    const resolveRect = (id) => {
      if (rects && rects[id]) {
        return rects[id];
      }
      const node = nodes && nodes[id];
      if (!node) {
        return null;
      }
      const position = node.position || { x: 0, y: 0 };
      return {
        left: position.x,
        top: position.y,
        width: DEFAULT_NODE_WIDTH,
        height: DEFAULT_NODE_HEIGHT
      };
    };

    const SIDE_VECTORS = {
      left: { x: -1, y: 0 },
      right: { x: 1, y: 0 },
      top: { x: 0, y: -1 },
      bottom: { x: 0, y: 1 }
    };

    const getAnchor = (rect, side) => {
      switch (side) {
        case 'left':
          return { x: rect.left, y: rect.top + rect.height / 2 };
        case 'right':
          return { x: rect.left + rect.width, y: rect.top + rect.height / 2 };
        case 'top':
          return { x: rect.left + rect.width / 2, y: rect.top };
        case 'bottom':
          return { x: rect.left + rect.width / 2, y: rect.top + rect.height };
        default:
          return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
      }
    };

    const offsetPoint = (point, side, distance) => {
      if (!distance) {
        return point;
      }
      const vector = SIDE_VECTORS[side] || { x: 0, y: 0 };
      return {
        x: point.x + vector.x * distance,
        y: point.y + vector.y * distance
      };
    };

    const pickConnection = (sourceRect, targetRect) => {
      const sourceCenter = {
        x: sourceRect.left + sourceRect.width / 2,
        y: sourceRect.top + sourceRect.height / 2
      };
      const targetCenter = {
        x: targetRect.left + targetRect.width / 2,
        y: targetRect.top + targetRect.height / 2
      };
      const dx = targetCenter.x - sourceCenter.x;
      const dy = targetCenter.y - sourceCenter.y;

      if (Math.abs(dx) > Math.abs(dy)) {
        return {
          sourceSide: dx >= 0 ? 'right' : 'left',
          targetSide: dx >= 0 ? 'left' : 'right',
          orientation: 'horizontal'
        };
      }

      return {
        sourceSide: dy >= 0 ? 'bottom' : 'top',
        targetSide: dy >= 0 ? 'top' : 'bottom',
        orientation: 'vertical'
      };
    };

    const cubicPoint = (p0, p1, p2, p3, t) => {
      const mt = 1 - t;
      return (
        mt * mt * mt * p0 +
        3 * mt * mt * t * p1 +
        3 * mt * t * t * p2 +
        t * t * t * p3
      );
    };

    return h(
      'svg',
      {
        className: 'link-canvas',
        width: '100%',
        height: '100%',
        style: {
          position: 'absolute',
          top: 0,
          left: 0,
          transform: `translate(${pan.x}px, ${pan.y}px)`
        }
      },
      edges.map((edge) => {
        if (!edge || edge.from === edge.to) {
          return null;
        }

        const source = resolveRect(edge.from);
        const target = resolveRect(edge.to);

        if (!source || !target) {
          return null;
        }

        const { sourceSide, targetSide, orientation } = pickConnection(source, target);
        const sourceAnchor = getAnchor(source, sourceSide);
        const targetAnchor = getAnchor(target, targetSide);
        const baseDx = targetAnchor.x - sourceAnchor.x;
        const baseDy = targetAnchor.y - sourceAnchor.y;
        const baseDistance = Math.hypot(baseDx, baseDy);
        const startOffset = Math.min(
          16,
          Math.min(baseDistance * 0.5, Math.max(baseDistance * 0.3, 4))
        );
        const startPoint = offsetPoint(sourceAnchor, sourceSide, startOffset);

        let arrowVec = {
          x: targetAnchor.x - startPoint.x,
          y: targetAnchor.y - startPoint.y
        };
        let arrowLength = Math.hypot(arrowVec.x, arrowVec.y);
        if (!arrowLength || !Number.isFinite(arrowLength)) {
          const fallback = SIDE_VECTORS[targetSide] || { x: 1, y: 0 };
          arrowVec = { x: -fallback.x, y: -fallback.y };
          arrowLength = Math.hypot(arrowVec.x, arrowVec.y);
        }
        const safeArrowLength = arrowLength || 1;
        let directionVector = {
          x: arrowVec.x / safeArrowLength,
          y: arrowVec.y / safeArrowLength
        };
        if (!Number.isFinite(directionVector.x) || !Number.isFinite(directionVector.y)) {
          const fallbackVector = SIDE_VECTORS[sourceSide] || { x: 1, y: 0 };
          const fallbackLength = Math.hypot(fallbackVector.x, fallbackVector.y) || 1;
          directionVector = {
            x: fallbackVector.x / fallbackLength,
            y: fallbackVector.y / fallbackLength
          };
        }

        let headLength = Math.min(12, Math.max(4, safeArrowLength * 0.25));
        if (headLength > safeArrowLength - 2) {
          headLength = Math.max(safeArrowLength * 0.5, safeArrowLength - 2);
        }
        if (headLength <= 0) {
          headLength = safeArrowLength * 0.5;
        }

        const lineEnd = {
          x: targetAnchor.x - directionVector.x * headLength,
          y: targetAnchor.y - directionVector.y * headLength
        };

        const pathDistance = Math.hypot(lineEnd.x - startPoint.x, lineEnd.y - startPoint.y);
        const dynamicMin = pathDistance < 80 ? Math.max(pathDistance * 0.45, 8) : 40;
        const baseCurve = pathDistance * 0.5;
        const curve = Math.min(220, Math.max(dynamicMin, baseCurve));
        const startVector = SIDE_VECTORS[sourceSide] || { x: 0, y: 0 };

        let control1;
        let control2;

        if (orientation === 'horizontal') {
          const deltaY = lineEnd.y - startPoint.y;
          control1 = {
            x: startPoint.x + startVector.x * curve,
            y: startPoint.y + deltaY * 0.25
          };
          control2 = {
            x: lineEnd.x - directionVector.x * curve,
            y: lineEnd.y - deltaY * 0.25
          };
        } else {
          const deltaX = lineEnd.x - startPoint.x;
          control1 = {
            x: startPoint.x + deltaX * 0.25,
            y: startPoint.y + startVector.y * curve
          };
          control2 = {
            x: lineEnd.x - deltaX * 0.25,
            y: lineEnd.y - directionVector.y * curve
          };
        }

        const path = [
          `M ${startPoint.x} ${startPoint.y}`,
          `C ${control1.x} ${control1.y} ${control2.x} ${control2.y} ${lineEnd.x} ${lineEnd.y}`
        ].join(' ');

        const arrowTipX = targetAnchor.x;
        const arrowTipY = targetAnchor.y;
        const angle = Math.atan2(arrowTipY - lineEnd.y, arrowTipX - lineEnd.x);
        const leftX = arrowTipX - headLength * Math.cos(angle - Math.PI / 6);
        const leftY = arrowTipY - headLength * Math.sin(angle - Math.PI / 6);
        const rightX = arrowTipX - headLength * Math.cos(angle + Math.PI / 6);
        const rightY = arrowTipY - headLength * Math.sin(angle + Math.PI / 6);
        const arrowHead = `M ${arrowTipX} ${arrowTipY} L ${leftX} ${leftY} L ${rightX} ${rightY} Z`;

        const labelX = cubicPoint(startPoint.x, control1.x, control2.x, lineEnd.x, 0.5);
        const labelY = cubicPoint(startPoint.y, control1.y, control2.y, lineEnd.y, 0.5) - 8;

        return h(
          'g',
          { key: edge.id, className: 'link-edge' },
          [
            h('path', {
              d: path,
              fill: 'none',
              stroke: '#38bdf8',
              'stroke-width': 3,
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
              opacity: 0.9
            }),
            h('path', {
              d: arrowHead,
              fill: '#38bdf8',
              opacity: 0.95
            }),
            edge.label
              ? h(
                  'text',
                  {
                    x: labelX,
                    y: labelY,
                    className: 'edge-label'
                  },
                  edge.label
                )
              : null
          ]
        );
      })
    );
  }

  function ConfigPanel({
    flows,
    currentFlow,
    selection,
    dispatch,
    aggregatedFunctions,
    onNavigateFlow
  }) {
    // SIEMPRE obtener el nodo más actualizado desde flows
    const actualFlow = selection ? flows[selection.flowId] : currentFlow;
    const node = selection && actualFlow ? actualFlow.nodes[selection.nodeId] : null;
    
    console.log('🔧 ConfigPanel render:', {
      selectionNodeId: selection?.nodeId,
      flowId: selection?.flowId,
      hasActualFlow: !!actualFlow,
      hasNode: !!node,
      nodeTransitions: node?.transitions
    });
    return h('aside', { className: 'config-panel' }, [
      h('div', { className: 'section-header' }, 'Configuration'),
      h(
        'div',
        { className: 'config-content' },
        node && actualFlow
          ? [
              h(FlowBreadcrumb, { flow: actualFlow, flows, onNavigate: onNavigateFlow }),
              h(NodeGeneralSettings, {
                flow: actualFlow,
                node,
                dispatch
              }),
              renderNodeEditor({
                node,
                flow: actualFlow,
                dispatch,
                aggregatedFunctions,
                flows,
                onNavigateFlow
              })
            ]
          : h('div', { className: 'empty-state' }, 'Select a node to configure its behaviour.')
      )
    ]);
  }

  function FlowBreadcrumb({ flow, flows, onNavigate }) {
    const items = [];
    let cursor = flow;
    while (cursor) {
      items.unshift(cursor);
      cursor = cursor.parent ? flows[cursor.parent.flowId] : null;
    }
    return h(
      'div',
      { className: 'flow-breadcrumb' },
      items.map((item, index) =>
        h(
          'button',
          {
            key: item.id,
            className: index === items.length - 1 ? 'active' : '',
            onClick: () => onNavigate(item.id)
          },
          item.label || item.id
        )
      )
    );
  }

  function supportsNextTransition(type) {
    return ['Task', 'Pass', 'Wait', 'Map', 'Parallel'].includes(type);
  }

  function NextStateSelect({ node, nextOptions, onChange }) {
    const currentValue = node.transitions.next || '';

    const handleChange = (event) => {
      const newValue = event.target.value;
      onChange(newValue ? newValue : null);
    };

    const renderOption = (option) =>
      h(
        'option',
        {
          key: option.id,
          value: option.id,
          selected: option.id === currentValue
        },
        option.label
      );

    return h(
      'select',
      {
        value: currentValue,
        disabled: node.transitions.end,
        onChange: handleChange
      },
      [
        h('option', { value: '', selected: currentValue === '' }, '— None —'),
        ...nextOptions.map(renderOption)
      ]
    );
  }

  function NodeGeneralSettings({ flow, node, dispatch }) {
    console.log('🔧 NodeGeneralSettings render:', {
      nodeId: node.id,
      nodeName: node.name,
      currentNext: node.transitions.next,
      allTransitions: node.transitions
    });

    const nextOptions = flow.order
      .filter((id) => id !== node.id)
      .map((id) => ({ id, label: flow.nodes[id].name }));

    console.log('🔧 NextOptions disponibles:', nextOptions);

    const handleNameChange = useCallback((event) => {
      const value = event.target.value;
      // Usar timeout para evitar updates constantes que causan pérdida de foco
      clearTimeout(handleNameChange.timeoutId);
      handleNameChange.timeoutId = setTimeout(() => {
        dispatch({
          type: 'UPDATE_NODE',
          flowId: flow.id,
          nodeId: node.id,
          changes: { name: value }
        });
      }, 300);
    }, [dispatch, flow.id, node.id]);

    const handleCommentChange = (event) => {
      dispatch({
        type: 'UPDATE_NODE',
        flowId: flow.id,
        nodeId: node.id,
        changes: { comment: event.target.value }
      });
    };

    const toggleEnd = () => {
      dispatch({
        type: 'UPDATE_NODE',
        flowId: flow.id,
        nodeId: node.id,
        changes: {
          transitions: {
            end: !node.transitions.end,
            next: node.transitions.end ? node.transitions.next : null
          }
        }
      });
    };

    const handleNextChange = (nextValue) => {
      console.log('🔄 handleNextChange:', {
        from: node.transitions.next,
        to: nextValue,
        nodeId: node.id
      });
      dispatch({
        type: 'UPDATE_NODE',
        flowId: flow.id,
        nodeId: node.id,
        changes: { transitions: { next: nextValue } }
      });
    };

    const removeNode = () => {
      if (window.confirm(`Remove node ${node.name}?`)) {
        dispatch({ type: 'REMOVE_NODE', flowId: flow.id, nodeId: node.id });
      }
    };

    const setAsStart = () => {
      dispatch({ type: 'SET_FLOW_START', flowId: flow.id, nodeId: node.id });
    };

    return h(Fragment, null, [
      h('div', { className: 'form-field' }, [
        h('label', null, 'State name'),
        h('input', {
          value: node.name,
          onChange: handleNameChange
        })
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'Comment'),
        h('textarea', {
          value: node.comment || '',
          onInput: handleCommentChange,
          placeholder: 'Optional description'
        })
      ]),
      h('div', { className: 'button-line' }, [
        h(
          'button',
          {
            onClick: setAsStart,
            disabled: flow.startNodeId === node.id
          },
          flow.startNodeId === node.id ? 'Start state' : 'Mark as start'
        ),
        h(
          'button',
          {
            onClick: removeNode,
            style: { background: 'rgba(248,113,113,0.2)', color: 'rgba(248,113,113,0.9)' }
          },
          'Remove'
        )
      ]),
      supportsNextTransition(node.type)
        ? h('div', { className: 'form-field' }, [
            h('label', null, 'Next state'),
            h(NextStateSelect, { node, nextOptions, onChange: handleNextChange })
          ])
        : null,
      h('div', { className: 'switch-row' }, [
        h('label', null, 'Marks end of the flow'),
        h('div', {
          className: 'toggle',
          'data-active': node.transitions.end ? 'true' : 'false',
          onClick: toggleEnd
        })
      ])
    ]);
  }

  function renderNodeEditor({ node, flow, dispatch, aggregatedFunctions, flows, onNavigateFlow }) {
    switch (node.type) {
      case 'Task':
        return h(TaskEditor, { node, flowId: flow.id, dispatch, aggregatedFunctions });
      case 'Pass':
        return h(PassEditor, { node, flowId: flow.id, dispatch });
      case 'Choice':
        return h(ChoiceEditor, { node, flow, dispatch });
      case 'Wait':
        return h(WaitEditor, { node, flowId: flow.id, dispatch });
      case 'Map':
        return h(MapEditor, { node, flowId: flow.id, dispatch, flows, onNavigateFlow });
      case 'Parallel':
        return h(ParallelEditor, { node, flowId: flow.id, dispatch, flows, onNavigateFlow });
      case 'Fail':
        return h(FailEditor, { node, flowId: flow.id, dispatch });
      case 'Succeed':
        return h(SucceedEditor, { node });
      default:
        return h('div', null, 'No editor available for this state.');
    }
  }

  function ParametersEditor({ parameters, onChange, title }) {
    const addParameter = () => {
      const next = parameters.concat({
        id: createId('param'),
        name: '',
        value: '',
        mode: 'value'
      });
      onChange(next);
    };

    const updateParameter = (index, changes) => {
      const next = parameters.map((param, idx) => (idx === index ? { ...param, ...changes } : param));
      onChange(next);
    };

    const removeParameter = (index) => {
      const next = parameters.filter((_, idx) => idx !== index);
      onChange(next);
    };

    return h('div', { className: 'form-field' }, [
      h('label', null, title || 'Parameters'),
      h(
        'div',
        { className: 'parameters' },
        [
          parameters.length
            ? parameters.map((param, index) =>
                h('div', { className: 'parameter-item', key: param.id }, [
                  h('input', {
                    placeholder: 'Key',
                    value: param.name,
                    onInput: (event) => updateParameter(index, { name: event.target.value })
                  }),
                  h('select', {
                    value: param.mode,
                    onChange: (event) => updateParameter(index, { mode: event.target.value })
                  }, [
                    h('option', { value: 'value' }, 'Value'),
                    h('option', { value: 'path' }, 'JSONPath')
                  ]),
                  h('input', {
                    placeholder: param.mode === 'path' ? '$.path' : 'Value',
                    value: param.value,
                    onInput: (event) => updateParameter(index, { value: event.target.value })
                  }),
                  h(
                    'button',
                    { onClick: () => removeParameter(index), title: 'Remove parameter' },
                    '×'
                  )
                ])
              )
            : h('div', { className: 'empty-state' }, 'No parameters defined.')
        ].concat([
          h(
            'button',
            {
              onClick: addParameter,
              style: {
                marginTop: '12px',
                width: '100%'
              }
            },
            'Add parameter'
          )
        ])
      )
    ]);
  }

  function TaskEditor({ node, flowId, dispatch, aggregatedFunctions }) {
    const config = node.config;

    const updateFunctionFields = (fields) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => {
          cfg.functionFields = fields;
        }
      });
    };

    const updateParameters = (parameters) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => {
          cfg.parameters = parameters;
        }
      });
    };

    const ensureVersionField = (fields, versions) => {
      let nextFields = fields.slice();
      const versionIndex = nextFields.findIndex((field) => field.key === 'Version');
      if (versions && versions.length) {
        if (versionIndex === -1) {
          nextFields.push({ id: createId('fn'), key: 'Version', value: versions[0].version || '' });
        } else if (!nextFields[versionIndex].value) {
          nextFields[versionIndex].value = versions[0].version || '';
        }
      } else if (versionIndex !== -1) {
        nextFields.splice(versionIndex, 1);
      }
      return nextFields;
    };

    const handleFunctionSelect = (event) => {
      const value = event.target.value;
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => {
          const fields = cfg.functionFields.slice();
          const nameField = fields.find((field) => field.key === 'Name');
          if (nameField) {
            nameField.value = value;
          } else {
            fields.unshift({ id: createId('fn'), key: 'Name', value, required: true });
          }
          const selected = aggregatedFunctions.find((fn) => fn.name === value);
          cfg.functionFields = ensureVersionField(fields, selected ? selected.versions : null);
        }
      });
    };

    const handleVersionSelect = (event) => {
      const value = event.target.value;
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => {
          cfg.functionFields = cfg.functionFields.map((field) =>
            field.key === 'Version' ? { ...field, value } : field
          );
        }
      });
    };

    const handleFieldChange = (index, changes) => {
      const next = config.functionFields.map((field, idx) =>
        idx === index ? { ...field, ...changes } : field
      );
      updateFunctionFields(next);
    };

    const addField = () => {
      updateFunctionFields(
        config.functionFields.concat({ id: createId('fn'), key: '', value: '' })
      );
    };

    const removeField = (index) => {
      const field = config.functionFields[index];
      if (field && field.required) {
        return;
      }
      updateFunctionFields(config.functionFields.filter((_, idx) => idx !== index));
    };

    const nameField = config.functionFields.find((field) => field.key === 'Name');
    const selectedFunction = nameField
      ? aggregatedFunctions.find((item) => item.name === nameField.value)
      : null;
    const versions = selectedFunction ? selectedFunction.versions || [] : [];

    const updatePathField = (key) => (event) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => {
          cfg[key] = event.target.value;
        }
      });
    };

    return h(Fragment, null, [
      h('div', { className: 'form-field' }, [
        h('label', null, 'Function catalog'),
        h(
          'select',
          {
            value: nameField ? nameField.value : '',
            onChange: handleFunctionSelect
          },
          [
            h('option', { value: '' }, '— Select function —'),
            ...aggregatedFunctions.map((fn) =>
              h('option', { key: fn.name, value: fn.name }, fn.name)
            )
          ]
        )
      ]),
      versions.length
        ? h('div', { className: 'form-field' }, [
            h('label', null, 'Version'),
            h(
              'select',
              {
                value: config.functionFields.find((field) => field.key === 'Version')?.value || '',
                onChange: handleVersionSelect
              },
              versions.map((version) =>
                h('option', { key: version.version, value: version.version }, version.version)
              )
            )
          ])
        : null,
      h('div', { className: 'form-field' }, [
        h('label', null, 'Function properties'),
        h(
          'div',
          { className: 'parameters' },
          [
            config.functionFields.map((field, index) =>
              h('div', { className: 'parameter-item', key: field.id }, [
                h('input', {
                  value: field.key,
                  onInput: (event) => handleFieldChange(index, { key: event.target.value }),
                  readOnly: field.required,
                  placeholder: 'Property'
                }),
                h('input', {
                  value: field.value,
                  onInput: (event) => handleFieldChange(index, { value: event.target.value }),
                  placeholder: 'Value'
                }),
                h(
                  'button',
                  {
                    onClick: () => removeField(index),
                    disabled: field.required
                  },
                  '×'
                )
              ])
            ),
            h(
              'button',
              {
                onClick: addField,
                style: { marginTop: '12px', width: '100%' }
              },
              'Add property'
            )
          ]
        )
      ]),
      h(ParametersEditor, {
        parameters: config.parameters,
        onChange: updateParameters,
        title: 'Parameters'
      }),
      h('div', { className: 'grid-row' }, [
        h('div', { className: 'form-field' }, [
          h('label', null, 'InputPath'),
          h('input', {
            value: config.inputPath || '',
            onInput: updatePathField('inputPath'),
            placeholder: '$'
          })
        ]),
        h('div', { className: 'form-field' }, [
          h('label', null, 'OutputPath'),
          h('input', {
            value: config.outputPath || '',
            onInput: updatePathField('outputPath'),
            placeholder: '$'
          })
        ])
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'ResultPath'),
        h('input', {
          value: config.resultPath || '',
          onInput: updatePathField('resultPath'),
          placeholder: '$'
        })
      ]),
      h('div', { className: 'grid-row' }, [
        h('div', { className: 'form-field' }, [
          h('label', null, 'Heartbeat (seconds)'),
          h('input', {
            value: config.heartbeatSeconds || '',
            onInput: updatePathField('heartbeatSeconds'),
            type: 'number',
            min: '0'
          })
        ]),
        h('div', { className: 'form-field' }, [
          h('label', null, 'Timeout (seconds)'),
          h('input', {
            value: config.timeoutSeconds || '',
            onInput: updatePathField('timeoutSeconds'),
            type: 'number',
            min: '0'
          })
        ])
      ])
    ]);
  }

  function PassEditor({ node, flowId, dispatch }) {
    const config = node.config;

    const updateConfig = (changes) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => Object.assign(cfg, changes)
      });
    };

    return h(Fragment, null, [
      h('div', { className: 'form-field' }, [
        h('label', null, 'Result payload'),
        h('textarea', {
          value: config.result || '',
          onInput: (event) => updateConfig({ result: event.target.value }),
          placeholder: config.resultIsJson ? '{ "key": "value" }' : 'Plain value'
        })
      ]),
      h('div', { className: 'switch-row' }, [
        h('label', null, 'Interpret as JSON'),
        h('div', {
          className: 'toggle',
          'data-active': config.resultIsJson ? 'true' : 'false',
          onClick: () => updateConfig({ resultIsJson: !config.resultIsJson })
        })
      ]),
      h(ParametersEditor, {
        parameters: config.parameters,
        onChange: (parameters) => updateConfig({ parameters }),
        title: 'Parameters'
      }),
      h('div', { className: 'grid-row' }, [
        h('div', { className: 'form-field' }, [
          h('label', null, 'InputPath'),
          h('input', {
            value: config.inputPath || '',
            onInput: (event) => updateConfig({ inputPath: event.target.value }),
            placeholder: '$'
          })
        ]),
        h('div', { className: 'form-field' }, [
          h('label', null, 'OutputPath'),
          h('input', {
            value: config.outputPath || '',
            onInput: (event) => updateConfig({ outputPath: event.target.value }),
            placeholder: '$'
          })
        ])
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'ResultPath'),
        h('input', {
          value: config.resultPath || '',
          onInput: (event) => updateConfig({ resultPath: event.target.value }),
          placeholder: '$'
        })
      ])
    ]);
  }

  function ChoiceEditor({ node, flow, dispatch }) {
    const config = node.config;
    const updateChoices = (choices) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId: flow.id,
        nodeId: node.id,
        updater: (cfg) => {
          cfg.choices = choices;
        }
      });
    };

    const addChoice = () => {
      updateChoices(
        (config.choices || []).concat({
          id: createId('choice'),
          variable: '',
          operator: 'StringEquals',
          value: '',
          next: null
        })
      );
    };

    const updateChoice = (index, changes) => {
      updateChoices(
        config.choices.map((choice, idx) => (idx === index ? { ...choice, ...changes } : choice))
      );
    };

    const removeChoice = (index) => {
      updateChoices(config.choices.filter((_, idx) => idx !== index));
    };

    const updateDefault = (event) => {
      dispatch({
        type: 'UPDATE_NODE',
        flowId: flow.id,
        nodeId: node.id,
        changes: { transitions: { default: event.target.value || null } }
      });
    };

    const nextOptions = flow.order
      .filter((id) => id !== node.id)
      .map((id) => ({ id, label: flow.nodes[id].name }));

    return h(Fragment, null, [
      h('div', { className: 'notice warning' }, 'Define comparison rules. The first matching rule determines the branch execution.'),
      (config.choices || []).map((choice, index) =>
        h('div', { className: 'parameters', key: choice.id }, [
          h('div', { className: 'form-field' }, [
            h('label', null, 'Variable'),
            h('input', {
              value: choice.variable || '',
              onInput: (event) => updateChoice(index, { variable: event.target.value }),
              placeholder: '$.path'
            })
          ]),
          h('div', { className: 'form-field' }, [
            h('label', null, 'Operator'),
            h(
              'select',
              {
                value: choice.operator,
                onChange: (event) => updateChoice(index, { operator: event.target.value })
              },
              CHOICE_OPERATORS.map((operator) =>
                h('option', { key: operator, value: operator }, operator)
              )
            )
          ]),
          h('div', { className: 'form-field' }, [
            h('label', null, 'Value'),
            h('input', {
              value: choice.value || '',
              onInput: (event) => updateChoice(index, { value: event.target.value })
            })
          ]),
          h('div', { className: 'form-field' }, [
            h('label', null, 'Next'),
            h(
              'select',
              {
                value: choice.next || '',
                onChange: (event) => updateChoice(index, { next: event.target.value || null })
              },
              [
                h('option', { value: '' }, '— Select —'),
                ...nextOptions.map((option) =>
                  h('option', { key: option.id, value: option.id }, option.label)
                )
              ]
            )
          ]),
          h(
            'button',
            {
              onClick: () => removeChoice(index),
              style: { marginTop: '8px', background: 'rgba(248,113,113,0.2)', color: 'rgba(248,113,113,0.9)' }
            },
            'Remove rule'
          )
        ])
      ),
      h(
        'button',
        {
          onClick: addChoice,
          style: { marginTop: '12px', width: '100%' }
        },
        'Add rule'
      ),
      h('div', { className: 'form-field' }, [
        h('label', null, 'Default branch'),
        h(
          'select',
          {
            value: node.transitions.default || '',
            onChange: updateDefault
          },
          [
            h('option', { value: '' }, '— None —'),
            ...nextOptions.map((option) =>
              h('option', { key: option.id, value: option.id }, option.label)
            )
          ]
        )
      ])
    ]);
  }

  function WaitEditor({ node, flowId, dispatch }) {
    const config = node.config;
    const updateConfig = (changes) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => Object.assign(cfg, changes)
      });
    };

    const renderModeField = () => {
      switch (config.mode) {
        case 'seconds':
          return h('input', {
            type: 'number',
            min: '0',
            value: config.seconds || '',
            onInput: (event) => updateConfig({ seconds: event.target.value }),
            placeholder: '10'
          });
        case 'timestamp':
          return h('input', {
            type: 'text',
            value: config.timestamp || '',
            onInput: (event) => updateConfig({ timestamp: event.target.value }),
            placeholder: '2024-01-01T00:00:00Z'
          });
        case 'secondsPath':
          return h('input', {
            type: 'text',
            value: config.secondsPath || '',
            onInput: (event) => updateConfig({ secondsPath: event.target.value }),
            placeholder: '$.wait_time'
          });
        case 'timestampPath':
          return h('input', {
            type: 'text',
            value: config.timestampPath || '',
            onInput: (event) => updateConfig({ timestampPath: event.target.value }),
            placeholder: '$.target_date'
          });
        default:
          return null;
      }
    };

    return h(Fragment, null, [
      h('div', { className: 'form-field' }, [
        h('label', null, 'Mode'),
        h(
          'select',
          {
            value: config.mode,
            onChange: (event) => updateConfig({ mode: event.target.value })
          },
          WAIT_MODES.map((mode) => h('option', { key: mode.id, value: mode.id }, mode.label))
        )
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'Value'),
        renderModeField()
      ]),
      h('div', { className: 'grid-row' }, [
        h('div', { className: 'form-field' }, [
          h('label', null, 'InputPath'),
          h('input', {
            value: config.inputPath || '',
            onInput: (event) => updateConfig({ inputPath: event.target.value })
          })
        ]),
        h('div', { className: 'form-field' }, [
          h('label', null, 'OutputPath'),
          h('input', {
            value: config.outputPath || '',
            onInput: (event) => updateConfig({ outputPath: event.target.value })
          })
        ])
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'ResultPath'),
        h('input', {
          value: config.resultPath || '',
          onInput: (event) => updateConfig({ resultPath: event.target.value })
        })
      ])
    ]);
  }

  function MapEditor({ node, flowId, dispatch, flows, onNavigateFlow }) {
    const config = node.config;
    const updateConfig = (changes) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => Object.assign(cfg, changes)
      });
    };

    const iteratorFlowId = node.branchFlowIds[0];
    const iteratorFlow = iteratorFlowId ? flows[iteratorFlowId] : null;

    return h(Fragment, null, [
      h('div', { className: 'form-field' }, [
        h('label', null, 'ItemsPath'),
        h('input', {
          value: config.itemsPath || '',
          onInput: (event) => updateConfig({ itemsPath: event.target.value }),
          placeholder: '$.items'
        })
      ]),
      h(ParametersEditor, {
        parameters: config.parameters,
        onChange: (parameters) => updateConfig({ parameters }),
        title: 'Parameters'
      }),
      h('div', { className: 'form-field' }, [
        h('label', null, 'ResultPath'),
        h('input', {
          value: config.resultPath || '',
          onInput: (event) => updateConfig({ resultPath: event.target.value })
        })
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'Max concurrency'),
        h('input', {
          type: 'number',
          min: '0',
          value: config.maxConcurrency || '',
          onInput: (event) => updateConfig({ maxConcurrency: event.target.value })
        })
      ]),
      iteratorFlow
        ? h('div', { className: 'branch-card' }, [
            h('span', null, iteratorFlow.label || 'Iterator'),
            h(
              'button',
              { onClick: () => onNavigateFlow(iteratorFlow.id) },
              'Edit iterator'
            )
          ])
        : null
    ]);
  }

  function ParallelEditor({ node, flowId, dispatch, flows, onNavigateFlow }) {
    const branches = node.branchFlowIds || [];

    const addBranch = () => {
      dispatch({ type: 'ADD_PARALLEL_BRANCH', flowId, nodeId: node.id });
    };

    const removeBranch = (index) => {
      dispatch({ type: 'REMOVE_PARALLEL_BRANCH', flowId, nodeId: node.id, index });
    };

    const renderBranch = (branchId, index) => {
      const branch = flows[branchId];
      const options = branch
        ? branch.order.map((id) => ({ id, label: branch.nodes[id].name }))
        : [];
      const startNodeId = branch && branch.startNodeId ? branch.startNodeId : '';
      const hasNodes = options.length > 0;

      const handleStartChange = (event) => {
        const value = event.target.value;
        if (!value || !branch) {
          return;
        }
        dispatch({ type: 'SET_FLOW_START', flowId: branchId, nodeId: value });
      };

      return h('div', { className: 'branch-card', key: branchId }, [
        h('div', { className: 'branch-card-header' }, [
          h('span', { className: 'branch-name' }, branch ? branch.label : `Branch ${index + 1}`),
          h('div', { className: 'branch-actions' }, [
            h(
              'button',
              { onClick: () => onNavigateFlow(branchId) },
              'Open'
            ),
            branches.length > 1
              ? h(
                  'button',
                  {
                    onClick: () => removeBranch(index),
                    style: {
                      background: 'rgba(248,113,113,0.2)',
                      color: 'rgba(248,113,113,0.9)'
                    }
                  },
                  'Remove'
                )
              : null
          ])
        ]),
        hasNodes
          ? h('div', { className: 'form-field condensed' }, [
              h('label', null, 'Start state'),
              h(
                'select',
                {
                  value: startNodeId,
                  onChange: handleStartChange
                },
                [
                  h('option', { value: '' }, '— Select —'),
                  ...options.map((option) =>
                    h('option', { key: option.id, value: option.id }, option.label)
                  )
                ]
              )
            ])
          : h('div', { className: 'branch-hint' }, 'Add states to this branch to choose where it starts.')
      ]);
    };

    return h(Fragment, null, [
      branches.length
        ? branches.map((branchId, index) => renderBranch(branchId, index))
        : h('div', { className: 'empty-state' }, 'No branches defined yet.'),
      h(
        'button',
        {
          onClick: addBranch,
          style: { marginTop: '12px', width: '100%' }
        },
        'Add branch'
      )
    ]);
  }

  function FailEditor({ node, flowId, dispatch }) {
    const config = node.config;
    const updateConfig = (changes) => {
      dispatch({
        type: 'UPDATE_NODE_CONFIG',
        flowId,
        nodeId: node.id,
        updater: (cfg) => Object.assign(cfg, changes)
      });
    };

    return h(Fragment, null, [
      h('div', { className: 'form-field' }, [
        h('label', null, 'Error code'),
        h('input', {
          value: config.error || '',
          onInput: (event) => updateConfig({ error: event.target.value })
        })
      ]),
      h('div', { className: 'form-field' }, [
        h('label', null, 'Cause'),
        h('textarea', {
          value: config.cause || '',
          onInput: (event) => updateConfig({ cause: event.target.value })
        })
      ])
    ]);
  }

  function SucceedEditor() {
    return h('div', { className: 'notice' }, 'This state marks the flow as completed successfully. No additional configuration is required.');
  }

  function InstallCatalogModal({ onClose, onInstall, pending, error }) {
    const [form, setForm] = useState({
      pipUrl: '',
      alias: '',
      module: '',
      attribute: 'function_catalog',
      authType: 'none',
      username: '',
      password: '',
      token: ''
    });

    const updateField = (key, value) => {
      setForm({ ...form, [key]: value });
    };

    const submit = (event) => {
      event.preventDefault();
      onInstall(form);
    };

    return h('div', { className: 'modal-backdrop' }, [
      h(
        'form',
        { className: 'modal', onSubmit: submit },
        [
          h('header', null, 'Install function catalog'),
          h(
            'div',
            { className: 'modal-body' },
            [
              h('div', { className: 'form-field' }, [
                h('label', null, 'Repository URL or pip spec'),
                h('input', {
                  required: true,
                  value: form.pipUrl,
                onInput: (event) => updateField('pipUrl', event.target.value),
                placeholder: 'git+https://...#egg=package'
              })
            ]),
            h('div', { className: 'grid-row' }, [
              h('div', { className: 'form-field' }, [
                h('label', null, 'Alias (optional)'),
                h('input', {
                  value: form.alias,
                  onInput: (event) => updateField('alias', event.target.value)
                })
              ]),
              h('div', { className: 'form-field' }, [
                h('label', null, 'Module name'),
                h('input', {
                  value: form.module,
                  onInput: (event) => updateField('module', event.target.value),
                  placeholder: 'package.module'
                })
              ])
            ]),
            h('div', { className: 'form-field' }, [
              h('label', null, 'Attribute'),
              h('input', {
                value: form.attribute,
                onInput: (event) => updateField('attribute', event.target.value)
              })
            ]),
            h('div', { className: 'form-field' }, [
              h('label', null, 'Authentication'),
              h(
                'select',
                {
                  value: form.authType,
                  onChange: (event) => updateField('authType', event.target.value)
                },
                [
                  h('option', { value: 'none' }, 'None'),
                  h('option', { value: 'basic' }, 'Username & password'),
                  h('option', { value: 'token' }, 'Token')
                ]
              )
            ]),
            form.authType === 'basic'
              ? h('div', { className: 'grid-row' }, [
                  h('div', { className: 'form-field' }, [
                    h('label', null, 'Username'),
                    h('input', {
                      value: form.username,
                      onInput: (event) => updateField('username', event.target.value)
                    })
                  ]),
                  h('div', { className: 'form-field' }, [
                    h('label', null, 'Password'),
                    h('input', {
                      type: 'password',
                      value: form.password,
                      onInput: (event) => updateField('password', event.target.value)
                    })
                  ])
                ])
              : null,
            form.authType === 'token'
              ? h('div', { className: 'form-field' }, [
                  h('label', null, 'Access token'),
                  h('input', {
                    value: form.token,
                    onInput: (event) => updateField('token', event.target.value)
                  })
                ])
              : null,
              error ? h('div', { className: 'notice danger' }, error) : null,
              h('div', { style: { height: '1px' } })
            ]
          ),
          h('footer', null, [
            h(
              'button',
              { type: 'button', className: 'ghost', onClick: onClose },
              'Cancel'
            ),
            h(
              'button',
              { type: 'submit', className: 'primary', disabled: pending },
              pending ? 'Installing…' : 'Install'
            )
          ])
        ]
      )
    ]);
  }

  function ValidationSummary({ validation }) {
    if (validation.status !== 'invalid' || !validation.errors.length) {
      return null;
    }
    return h(
      'div',
      { className: 'validation-panel' },
      validation.errors.map((error, index) =>
        h('div', { className: 'error-item', key: index }, [
          h('strong', null, error.message),
          error.path && error.path.length
            ? h('span', null, `Path: ${error.path.join(' > ')}`)
            : null,
          error.validator ? h('span', null, `Validator: ${error.validator}`) : null
        ])
      )
    );
  }

  function App() {
    const [state, dispatch] = useReducer(reducer, null, createInitialState);
    const [nodeRects, setNodeRects] = useState({});
    const [installPending, setInstallPending] = useState(false);
    const [installError, setInstallError] = useState('');
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const canvasRef = useRef(null);
    const flow = state.flows[state.currentFlowId];

    // Exponer estado para debugging
    window.debugState = state;
    window.debugDispatch = dispatch;

    useCatalogs(dispatch);
    useToasts(state, dispatch);

    const handleMeasureNodeRect = useCallback((nodeId, rect) => {
      setNodeRects((prev) => {
        if (rect) {
          const existing = prev[nodeId];
          if (
            existing &&
            existing.left === rect.left &&
            existing.top === rect.top &&
            existing.width === rect.width &&
            existing.height === rect.height
          ) {
            return prev;
          }
          return { ...prev, [nodeId]: rect };
        }
        if (!prev[nodeId]) {
          return prev;
        }
        const next = { ...prev };
        delete next[nodeId];
        return next;
      });
    }, []);

    useEffect(() => {
      if (!flow) {
        return;
      }
      setPan({ x: 0, y: 0 });
    }, [flow && flow.id]);

    useEffect(() => {
      if (!flow) {
        setNodeRects({});
        return;
      }
      setNodeRects({});
    }, [flow && flow.id]);

    const edges = useMemo(() => computeEdges(flow), [flow, state.revision]);

    const handleDropNode = useCallback(
      (type, position) => {
        console.log('🎯 handleDropNode llamado:', { type, position, flowId: flow?.id });
        if (!flow) {
          console.error('No hay flow disponible');
          return;
        }
        dispatch({ type: 'ADD_NODE', flowId: flow.id, nodeType: type, position });
      },
      [dispatch, flow]
    );

    const handleSelectNode = useCallback(
      (nodeId) => {
        console.log('🎯 handleSelectNode llamado:', { nodeId, flowId: flow?.id });
        if (!flow) {
          console.error('No hay flow disponible para seleccionar nodo');
          return;
        }
        dispatch({ type: 'SET_SELECTION', selection: { flowId: flow.id, nodeId } });
      },
      [dispatch, flow]
    );

    const handleMoveNode = useCallback(
      (nodeId, position) => {
        console.log('🔄 handleMoveNode llamado:', { nodeId, position, flowId: flow?.id });
        if (!flow) {
          console.error('No hay flow disponible para mover nodo');
          return;
        }
        dispatch({ type: 'UPDATE_NODE_POSITION', flowId: flow.id, nodeId, position });
      },
      [dispatch, flow]
    );

    const handleNavigateFlow = useCallback(
      (flowId) => {
        dispatch({ type: 'NAVIGATE_FLOW', flowId });
      },
      [dispatch]
    );

    const handlePanChange = useCallback((nextPan) => {
      setPan((prev) => {
        if (prev.x === nextPan.x && prev.y === nextPan.y) {
          return prev;
        }
        return nextPan;
      });
    }, []);

    const handleDownload = () => {
      const payload = buildFlowExport(state);
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'dynaflow.json';
      link.click();
      URL.revokeObjectURL(url);
    };

    const handleValidate = () => {
      const payload = buildFlowExport(state);
      dispatch({ type: 'SET_VALIDATION', status: 'running', errors: [] });
      fetch('/api/flow/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flow: payload })
      })
        .then(async (response) => {
          const result = await response.json();
          if (!response.ok || !result.valid) {
            dispatch({ type: 'SET_VALIDATION', status: 'invalid', errors: result.errors || [] });
            dispatch({
              type: 'ADD_TOAST',
              toast: formatToast('Flow has validation issues.', 'error')
            });
          } else {
            dispatch({ type: 'SET_VALIDATION', status: 'valid', errors: [] });
            dispatch({
              type: 'ADD_TOAST',
              toast: formatToast('Flow looks good!', 'success')
            });
          }
        })
        .catch(() => {
          dispatch({ type: 'SET_VALIDATION', status: 'invalid', errors: [] });
          dispatch({
            type: 'ADD_TOAST',
            toast: formatToast('Validation failed. Check your server logs.', 'error')
          });
        });
    };

    const openInstallModal = () => {
      dispatch({ type: 'TOGGLE_INSTALL_MODAL', visible: true });
      setInstallError('');
    };

    const closeInstallModal = () => {
      dispatch({ type: 'TOGGLE_INSTALL_MODAL', visible: false });
      setInstallError('');
    };

    const handleInstallCatalog = (form) => {
      setInstallPending(true);
      setInstallError('');
      const body = {
        pip_url: form.pipUrl,
        alias: form.alias || undefined,
        module: form.module || undefined,
        attribute: form.attribute || undefined
      };
      if (form.authType === 'basic') {
        body.auth = {
          type: 'basic',
          username: form.username,
          password: form.password
        };
      } else if (form.authType === 'token') {
        body.auth = {
          type: 'token',
          token: form.token
        };
      }

      fetch('/api/catalogs/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
        .then(async (response) => {
          if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || 'Installation failed');
          }
          closeInstallModal();
          fetchCatalogs(dispatch);
          dispatch({
            type: 'ADD_TOAST',
            toast: formatToast('Catalog installed successfully', 'success')
          });
        })
        .catch((err) => {
          setInstallError(err.message);
        })
        .finally(() => setInstallPending(false));
    };

    const handleRefreshCatalog = (alias) => {
      fetch(`/api/catalogs/${encodeURIComponent(alias)}/refresh`, {
        method: 'POST'
      })
        .then((response) => response.json())
        .then(() => {
          fetchCatalogs(dispatch);
          dispatch({
            type: 'ADD_TOAST',
            toast: formatToast(`Catalog ${alias} refreshed`, 'success')
          });
        })
        .catch(() =>
          dispatch({
            type: 'ADD_TOAST',
            toast: formatToast(`Unable to refresh ${alias}`, 'error')
          })
        );
    };

    const handleRemoveCatalog = (alias) => {
      fetch(`/api/catalogs/${encodeURIComponent(alias)}`, {
        method: 'DELETE'
      })
        .then(() => {
          fetchCatalogs(dispatch);
          dispatch({
            type: 'ADD_TOAST',
            toast: formatToast(`Catalog ${alias} removed`, 'success')
          });
        })
        .catch(() =>
          dispatch({
            type: 'ADD_TOAST',
            toast: formatToast(`Unable to remove ${alias}`, 'error')
          })
        );
    };

    return h('div', { className: 'app-shell' }, [
      h(AppHeader, {
        flow,
        flows: state.flows,
        onDownload: handleDownload,
        onValidate: handleValidate,
        onOpenInstall: openInstallModal,
        onNavigateFlow: handleNavigateFlow,
        validation: state.validation
      }),
      h('div', { className: 'app-body' }, [
        h(Sidebar, {
          catalogs: state.catalogs.items,
          onRefreshCatalog: handleRefreshCatalog,
          onRemoveCatalog: handleRemoveCatalog,
          onAddNode: handleDropNode
        }),
        h(CanvasView, {
          flow,
          selection: state.selection,
          canvasRef,
          edges,
          nodeRects,
          onDropNode: handleDropNode,
          onSelectNode: handleSelectNode,
          onMoveNode: handleMoveNode,
          onOpenFlow: handleNavigateFlow,
          onMeasureNode: handleMeasureNodeRect,
          pan,
          onPanChange: handlePanChange
        }),
        h(ConfigPanel, {
          flows: state.flows,
          currentFlow: flow,
          selection: state.selection,
          dispatch,
          aggregatedFunctions: state.catalogs.aggregated,
          onNavigateFlow: handleNavigateFlow
        })
      ]),
      h(ValidationSummary, { validation: state.validation }),
      state.showInstallModal
        ? h(InstallCatalogModal, {
            onClose: closeInstallModal,
            onInstall: handleInstallCatalog,
            pending: installPending,
            error: installError
          })
        : null,
      h(ToastContainer, { toasts: state.toasts })
    ]);
  }

  render(h(App, null), document.getElementById('app'));
})();
