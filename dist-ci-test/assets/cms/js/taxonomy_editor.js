(function () {
  'use strict';
  function parseIndentation(text) {
    var rawLines = text.split('\n'), errors = [], lines = [];
    rawLines.forEach(function (raw, idx) {
      var trimEnd = raw.replace(/\s+$/, '');
      if (!trimEnd.trim() || trimEnd.trim().charAt(0) === '#') return;
      lines.push({ raw: trimEnd, lineNo: idx + 1 });
    });
    if (!lines.length) return { tree: null, errors: [] };
    var measured = lines.map(function (l) {
      var expanded = l.raw.replace(/\t/g, '    ');
      return { text: l.raw.trim(), leading: expanded.length - expanded.trimStart().length, lineNo: l.lineNo };
    });
    var unit = 0;
    for (var i = 0; i < measured.length; i++) if (measured[i].leading > 0) { unit = measured[i].leading; break; }
    var root = {}, stack = [{ level: -1, obj: root }], prevLevel = 0;
    measured.forEach(function (l) {
      var level = unit > 0 ? Math.round(l.leading / unit) : 0;
      if (level > prevLevel + 1) level = prevLevel + 1;
      while (stack.length > 1 && stack[stack.length - 1].level >= level) stack.pop();
      var parent = stack[stack.length - 1].obj;
      parent[l.text] = {};
      stack.push({ level: level, obj: parent[l.text] });
      prevLevel = level;
    });
    function nullifyLeaves(obj) {
      Object.keys(obj).forEach(function (k) {
        if (!Object.keys(obj[k]).length) obj[k] = null; else nullifyLeaves(obj[k]);
      });
      return obj;
    }
    return { tree: nullifyLeaves(root), errors: errors };
  }
  var totalNodes = 0;
  function renderPreviewTree(treeObj) {
    totalNodes = 0;
    var ul = document.createElement('ul');
    ul.className = 'tree-list';
    (function build(obj, ulEl) {
      Object.keys(obj).forEach(function (name) {
        totalNodes++;
        var li = document.createElement('li');
        li.textContent = name;
        ulEl.appendChild(li);
        if (obj[name] && typeof obj[name] === 'object') {
          var child = document.createElement('ul');
          child.className = 'tree-children';
          build(obj[name], child);
          li.appendChild(child);
        }
      });
    })(treeObj, ul);
    return ul;
  }
  var textarea = document.getElementById('texto-taxonomia');
  var previewEl = document.getElementById('preview-arbol');
  var totalEl = document.getElementById('preview-total');
  if (!textarea) return;
  function actualizarPreview() {
    var result = parseIndentation(textarea.value);
    if (!result.tree) {
      previewEl.innerHTML = '<p>El árbol aparecerá aquí…</p>';
      totalEl.textContent = '';
      return;
    }
    previewEl.innerHTML = '';
    previewEl.appendChild(renderPreviewTree(result.tree));
    totalEl.textContent = 'Total: ' + totalNodes + ' nodos';
  }
  textarea.addEventListener('input', function () { clearTimeout(window._taxDeb); window._taxDeb = setTimeout(actualizarPreview, 280); });
})();
