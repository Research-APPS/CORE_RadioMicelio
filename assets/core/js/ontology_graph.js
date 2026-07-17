(function () {
  var dataEl = document.getElementById('ontology-graph-data');
  var codeEl = document.getElementById('ontology-synth-code');
  if (!dataEl || !codeEl) return;

  var graph;
  try {
    graph = JSON.parse(dataEl.textContent);
  } catch (e) {
    codeEl.textContent = 'No se pudo cargar el grafo.';
    return;
  }

  var nodesById = {};
  (graph.nodes || []).forEach(function (n) { nodesById[n.id] = n; });

  var edgesByFrom = {};
  (graph.edges || []).forEach(function (e) {
    if (!edgesByFrom[e.from]) edgesByFrom[e.from] = [];
    edgesByFrom[e.from].push(e);
  });

  var plainText = '';

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function span(cls, text) {
    return '<span class="' + cls + '">' + escapeHtml(text) + '</span>';
  }

  function classLabel(node) {
    if (node.topic_url) {
      var cls = 'syn-class-link';
      if (node.inferred) cls += ' syn-class-inferred';
      return '<a href="' + escapeHtml(node.topic_url) + '" class="' + cls + '">' + escapeHtml(node.label) + '</a>';
    }
    var cls = 'syn-class';
    if (node.inferred) cls += ' syn-class-inferred';
    return span(cls, node.label);
  }

  function indent(level) {
    return '  '.repeat(level);
  }

  function buildSynthesis() {
    var project = (graph.nodes || []).find(function (n) { return n.kind === 'project'; });
    if (!project) {
      return { html: '<span class="ontology-empty">Sin datos ontológicos.</span>', text: '' };
    }

    var htmlLines = [];
    var textLines = [];

    htmlLines.push(
      span('syn-kw', '@notebook') + ' ' +
      span('syn-project', project.label) +
      (project.acron ? span('syn-muted', ' (' + project.acron + ')') : '')
    );
    textLines.push('@notebook ' + project.label + (project.acron ? ' (' + project.acron + ')' : ''));
    htmlLines.push('');
    textLines.push('');

    var cited = (edgesByFrom[project.id] || []).filter(function (e) { return e.kind === 'citation'; });
    cited.forEach(function (cite, idx) {
      var concept = nodesById[cite.to];
      if (!concept) return;

      if (idx > 0) {
        htmlLines.push('');
        textLines.push('');
      }

      htmlLines.push(span('syn-comment', '// ' + (concept.subject || 'Concepto')));
      textLines.push('// ' + (concept.subject || 'Concepto'));

      var classLine =
        span('syn-kw', '@class') + ' ' + classLabel(concept) +
        (concept.subject_slug ? ' ' + span('syn-tag', '#' + concept.subject_slug) : '');
      htmlLines.push(classLine);
      textLines.push('@class ' + concept.label + (concept.subject_slug ? ' #' + concept.subject_slug : ''));

      htmlLines.push(indent(1) + span('syn-kw', '@status') + ' ' + span('syn-prop-val', cite.label));
      textLines.push(indent(1) + '@status ' + cite.label);

      if (cite.note) {
        htmlLines.push(indent(1) + span('syn-kw', '@note') + ' ' + span('syn-prop-val', '"' + cite.note + '"'));
        textLines.push(indent(1) + '@note "' + cite.note + '"');
      }

      var props = (graph.nodes || []).filter(function (n) {
        return n.kind === 'property' && n.parent_concept === concept.id;
      });
      props.forEach(function (p) {
        var key = p.property_key || p.label.split(':')[0].trim();
        var val = p.property_value != null ? p.property_value : (p.label.split(':').slice(1).join(':').trim() || '');
        htmlLines.push(
          indent(1) + span('syn-kw', '@property') + ' ' +
          span('syn-prop-key', key) + span('syn-punct', ' = ') + span('syn-prop-val', '"' + val + '"')
        );
        textLines.push(indent(1) + '@property ' + key + ' = "' + val + '"');
      });

      var rels = (edgesByFrom[concept.id] || []).filter(function (e) { return e.kind === 'relation'; });
      rels.forEach(function (rel) {
        var target = nodesById[rel.to];
        var targetLabel = target ? target.label : rel.to;
        htmlLines.push(
          indent(1) + span('syn-kw', '@relation') + ' ' +
          span('syn-rel-type', rel.label) + ' ' +
          span('syn-arrow', '→ ') +
          (target ? classLabel(target) : span('syn-class', targetLabel))
        );
        textLines.push(indent(1) + '@relation ' + rel.label + ' → ' + targetLabel);
      });
    });

    if (!cited.length) {
      htmlLines.push('');
      htmlLines.push(span('syn-muted', '// Sin marcadores en este cuaderno'));
      textLines.push('');
      textLines.push('// Sin marcadores en este cuaderno');
    }

    return { html: htmlLines.join('\n'), text: textLines.join('\n') };
  }

  var synthesis = buildSynthesis();
  plainText = synthesis.text;
  codeEl.innerHTML = synthesis.html;

  document.querySelectorAll('[data-action="copy"]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (!plainText) return;
      navigator.clipboard.writeText(plainText).then(function () {
        btn.textContent = 'Copiado';
        setTimeout(function () { btn.textContent = 'Copiar síntesis'; }, 1200);
      });
    });
  });
})();
