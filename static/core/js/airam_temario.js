(function () {
  var script = document.querySelector('script[data-taxonomy-slug]');
  if (!script) return;

  var taxonomySlug = script.getAttribute('data-taxonomy-slug');
  var taxonomyName = script.getAttribute('data-taxonomy-name') || taxonomySlug;
  var storageKey = 'airam_session_' + taxonomySlug;
  var queueKey = 'airam_queue_' + taxonomySlug;

  var panel = document.getElementById('airam-temario-panel');
  var dialog = document.getElementById('airam-resume-dialog');
  if (!panel) return;

  var bodyEl = panel.querySelector('[data-airam-body]');
  var titleEl = panel.querySelector('[data-airam-session-title]');
  var granularityEl = panel.querySelector('[data-airam-granularity]');
  var continueBtn = panel.querySelector('[data-airam-action="continue"]');
  var bookmarkBtn = panel.querySelector('[data-airam-action="bookmark"]');
  var startCombinedBtn = panel.querySelector('[data-airam-action="start-combined"]');
  var clearQueueBtn = panel.querySelector('[data-airam-action="clear-queue"]');
  var exportQueueBtn = panel.querySelector('[data-airam-action="export-queue-rdf"]');
  var queueEl = panel.querySelector('[data-airam-queue]');
  var classesEl = panel.querySelector('[data-airam-classes]');
  var resumeText = dialog && dialog.querySelector('[data-airam-resume-text]');

  var currentSession = null;
  var pendingStart = null;

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function api(path, options) {
    options = options || {};
    var headers = options.headers || {};
    headers['Content-Type'] = 'application/json';
    if (csrfToken()) headers['X-CSRFToken'] = csrfToken();
    return fetch('/airam/' + path, Object.assign({}, options, { headers: headers }))
      .then(function (r) {
        return r.json().then(function (data) {
          if (!r.ok) throw new Error(data.error || 'Error AIRAM');
          return data;
        });
      });
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function loadQueue() {
    try {
      return JSON.parse(localStorage.getItem(queueKey) || '[]');
    } catch (e) {
      return [];
    }
  }

  function saveQueue(queue) {
    localStorage.setItem(queueKey, JSON.stringify(queue));
    renderQueue();
    syncQueueButtons();
  }

  function queueHas(uuid) {
    return loadQueue().some(function (item) { return item.uuid === uuid; });
  }

  function toggleQueueItem(uuid, label) {
    var queue = loadQueue();
    var idx = queue.findIndex(function (item) { return item.uuid === uuid; });
    if (idx >= 0) {
      queue.splice(idx, 1);
    } else {
      queue.push({ uuid: uuid, label: label });
    }
    saveQueue(queue);
  }

  function downloadBlob(content, filename, type) {
    var blob = new Blob([content], { type: type || 'application/octet-stream' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function downloadFromResponse(r) {
    if (!r.ok) {
      return r.json().then(function (data) {
        throw new Error(data.error || 'Error al exportar RDF');
      });
    }
    var cd = r.headers.get('Content-Disposition') || '';
    var match = /filename="([^"]+)"/.exec(cd);
    var filename = match ? match[1] : 'temario.jsonld';
    return r.text().then(function (text) {
      downloadBlob(text, filename, r.headers.get('Content-Type'));
    });
  }

  function exportSessionRdf() {
    if (!currentSession) return Promise.resolve();
    return fetch('/airam/sessions/' + currentSession.uuid + '/rdf/?format=json', {
      headers: { 'X-CSRFToken': csrfToken() },
    }).then(downloadFromResponse);
  }

  function exportQueueRdf() {
    var queue = loadQueue();
    if (!queue.length) return Promise.resolve();
    return fetch('/airam/temario/rdf/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
      },
      body: JSON.stringify({
        format: 'json',
        taxonomy_slug: taxonomySlug,
        node_uuids: queue.map(function (q) { return q.uuid; }),
        granularity: granularityEl ? granularityEl.value : 'normal',
      }),
    }).then(downloadFromResponse);
  }

  function renderQueue() {
    var queue = loadQueue();
    document.querySelectorAll('[data-airam-queue-count]').forEach(function (el) {
      el.textContent = String(queue.length);
    });
    if (!queueEl) return;
    if (!queue.length) {
      queueEl.innerHTML = '<li class="airam-panel__queue-empty">Pulsa ⊕ en las clases que quieras incluir.</li>';
      if (startCombinedBtn) startCombinedBtn.disabled = true;
      if (exportQueueBtn) exportQueueBtn.disabled = true;
      return;
    }
    queueEl.innerHTML = queue.map(function (item) {
      return '<li class="airam-panel__queue-item">' +
        '<span>' + escapeHtml(item.label) + '</span>' +
        '<button type="button" class="airam-panel__queue-remove" data-queue-remove="' + item.uuid + '" aria-label="Quitar">×</button>' +
        '</li>';
    }).join('');
    if (startCombinedBtn) startCombinedBtn.disabled = queue.length < 1;
    if (exportQueueBtn) exportQueueBtn.disabled = queue.length < 1;
  }

  function syncQueueButtons() {
    document.querySelectorAll('.taxonomy-airam-queue-btn').forEach(function (btn) {
      var uuid = btn.getAttribute('data-node-uuid');
      var active = queueHas(uuid);
      if (currentSession && currentSession.combined_nodes) {
        active = currentSession.combined_nodes.some(function (n) { return n.uuid === uuid; });
      }
      btn.classList.toggle('taxonomy-airam-queue-btn--active', active);
    });
  }

  function renderSessionClasses(data) {
    if (!classesEl) return;
    var nodes = data.combined_nodes || [];
    if (!nodes.length || !data.uuid) {
      classesEl.hidden = true;
      classesEl.innerHTML = '';
      return;
    }
    classesEl.hidden = false;
    classesEl.innerHTML = nodes.map(function (node) {
      var removable = nodes.length > 1;
      return '<li class="airam-panel__class-item">' +
        '<span>' + escapeHtml(node.label) + '</span>' +
        (removable
          ? '<button type="button" class="airam-panel__class-remove" data-class-remove="' + node.uuid + '" aria-label="Quitar clase">×</button>'
          : '') +
        '</li>';
    }).join('');
  }

  function saveLocal(session) {
    if (session && session.uuid) {
      localStorage.setItem(storageKey, session.uuid);
    }
  }

  function getLocalId() {
    return localStorage.getItem(storageKey);
  }

  function renderView(data) {
    currentSession = data;
    titleEl.textContent = data.title || '';
    granularityEl.value = data.granularity || 'normal';
    renderSessionClasses(data);
    var view = data.view || {};
    var html = '';
    if (view.progress) {
      html += '<p class="airam-panel__progress">' + view.progress.current + ' / ' + view.progress.total + '</p>';
    }
    (view.paragraphs || []).forEach(function (p) {
      html += '<p>' + escapeHtml(p) + '</p>';
    });
    if (view.concepts && view.concepts.length) {
      html += '<p>';
      view.concepts.forEach(function (c, i) {
        if (i) html += ' ';
        html += '<button type="button" class="airam-panel__concept-btn" data-concept-uuid="' + c.uuid + '">' + escapeHtml(c.label) + '</button>';
      });
      html += '</p>';
    }
    if (data.is_bookmarked) {
      html += '<p class="airam-panel__saved">Temario guardado.</p>';
    }
    bodyEl.innerHTML = html;
    continueBtn.disabled = !view.can_continue;
    panel.hidden = false;
    saveLocal(data);
    syncQueueButtons();
  }

  function openPanel() {
    panel.hidden = false;
    renderQueue();
    syncQueueButtons();
  }

  function closePanel() {
    panel.hidden = true;
  }

  function createNew(nodeUuid, granularity, nodeUuids) {
    var payload = {
      taxonomy_slug: taxonomySlug,
      granularity: granularity || granularityEl.value,
    };
    if (nodeUuids && nodeUuids.length) {
      payload.node_uuids = nodeUuids;
    } else {
      payload.node_uuid = nodeUuid;
    }
    return api('sessions/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }).then(function (data) {
      if (nodeUuids && nodeUuids.length) {
        localStorage.removeItem(queueKey);
        renderQueue();
      }
      return renderView(data);
    });
  }

  function startSession(nodeUuid, granularity, forceNew, nodeUuids) {
    var localId = !forceNew && getLocalId();
    if (localId && !forceNew) {
      return api('sessions/' + localId + '/').then(renderView).catch(function () {
        localStorage.removeItem(storageKey);
        return createNew(nodeUuid, granularity, nodeUuids);
      });
    }
    return createNew(nodeUuid, granularity, nodeUuids);
  }

  function onAiramClick(btn) {
    var nodeUuid = btn.getAttribute('data-node-uuid');
    var label = btn.getAttribute('data-label');
    pendingStart = { nodeUuid: nodeUuid, label: label, nodeUuids: null };
    var localId = getLocalId();
    if (localId && dialog) {
      resumeText.textContent = 'Ya tienes un temario abierto sobre ' + taxonomyName + '. ¿Reanudar o empezar uno nuevo?';
      dialog.hidden = false;
      return;
    }
    startSession(nodeUuid, 'normal', true, null);
  }

  function onQueueClick(btn) {
    var nodeUuid = btn.getAttribute('data-node-uuid');
    var label = btn.getAttribute('data-label');

    if (currentSession) {
      var already = (currentSession.combined_nodes || []).some(function (n) { return n.uuid === nodeUuid; });
      if (already) {
        api('sessions/' + currentSession.uuid + '/', {
          method: 'PATCH',
          body: JSON.stringify({ action: 'remove_class', node_uuid: nodeUuid }),
        }).then(renderView);
      } else {
        api('sessions/' + currentSession.uuid + '/', {
          method: 'PATCH',
          body: JSON.stringify({ action: 'add_class', node_uuid: nodeUuid }),
        }).then(renderView);
      }
      openPanel();
      return;
    }

    toggleQueueItem(nodeUuid, label);
    openPanel();
  }

  document.addEventListener('click', function (e) {
    var queueBtn = e.target.closest('.taxonomy-airam-queue-btn');
    if (queueBtn) {
      e.preventDefault();
      e.stopPropagation();
      onQueueClick(queueBtn);
      return;
    }

    var airamBtn = e.target.closest('.taxonomy-airam-btn');
    if (airamBtn) {
      e.preventDefault();
      e.stopPropagation();
      onAiramClick(airamBtn);
      return;
    }

    if (e.target.closest('[data-airam-open-builder]')) {
      openPanel();
      return;
    }

    if (e.target.closest('[data-airam-action="close"]')) {
      closePanel();
      return;
    }

    if (e.target.closest('[data-airam-action="start-combined"]')) {
      var queue = loadQueue();
      if (!queue.length) return;
      pendingStart = {
        nodeUuid: queue[0].uuid,
        label: queue.map(function (q) { return q.label; }).join(' + '),
        nodeUuids: queue.map(function (q) { return q.uuid; }),
      };
      var localId = getLocalId();
      if (localId && dialog) {
        resumeText.textContent = 'Ya tienes un temario abierto. ¿Reanudar el anterior o empezar el temario combinado?';
        dialog.hidden = false;
        return;
      }
      startSession(queue[0].uuid, 'normal', true, queue.map(function (q) { return q.uuid; }));
      return;
    }

    if (e.target.closest('[data-airam-action="clear-queue"]')) {
      saveQueue([]);
      return;
    }

    var queueRemove = e.target.closest('[data-queue-remove]');
    if (queueRemove) {
      var uuid = queueRemove.getAttribute('data-queue-remove');
      saveQueue(loadQueue().filter(function (item) { return item.uuid !== uuid; }));
      return;
    }

    var classRemove = e.target.closest('[data-class-remove]');
    if (classRemove && currentSession) {
      api('sessions/' + currentSession.uuid + '/', {
        method: 'PATCH',
        body: JSON.stringify({
          action: 'remove_class',
          node_uuid: classRemove.getAttribute('data-class-remove'),
        }),
      }).then(renderView);
      return;
    }

    if (e.target.closest('[data-airam-action="continue"]') && currentSession) {
      api('sessions/' + currentSession.uuid + '/', {
        method: 'PATCH',
        body: JSON.stringify({ action: 'continue' }),
      }).then(renderView);
      return;
    }

    if (e.target.closest('[data-airam-action="bookmark"]') && currentSession) {
      api('sessions/' + currentSession.uuid + '/bookmark/', { method: 'POST', body: '{}' })
        .then(renderView);
      return;
    }

    if (e.target.closest('[data-airam-action="export-rdf"]') && currentSession) {
      exportSessionRdf().catch(function (err) { alert(err.message); });
      return;
    }

    if (e.target.closest('[data-airam-action="export-queue-rdf"]')) {
      exportQueueRdf().catch(function (err) { alert(err.message); });
      return;
    }

    var conceptBtn = e.target.closest('[data-concept-uuid]');
    if (conceptBtn && currentSession) {
      var conceptUuid = conceptBtn.getAttribute('data-concept-uuid');
      api('sessions/' + currentSession.uuid + '/', {
        method: 'PATCH',
        body: JSON.stringify({
          action: 'explore_concept',
          concept_uuid: conceptUuid,
        }),
      }).then(function (data) {
        renderView(data);
        if (window.AIRAM_WORKSPACE) {
          window.AIRAM_WORKSPACE.recordConcept(conceptUuid, 'visited');
        }
      });
      return;
    }

    if (dialog && !dialog.hidden) {
      if (e.target.closest('[data-airam-resume="resume"]') && pendingStart) {
        dialog.hidden = true;
        startSession(pendingStart.nodeUuid, 'normal', false, pendingStart.nodeUuids);
        pendingStart = null;
        return;
      }
      if (e.target.closest('[data-airam-resume="new"]') && pendingStart) {
        dialog.hidden = true;
        startSession(pendingStart.nodeUuid, 'normal', true, pendingStart.nodeUuids);
        pendingStart = null;
        return;
      }
      if (e.target.closest('[data-airam-resume="cancel"]')) {
        dialog.hidden = true;
        pendingStart = null;
      }
    }
  });

  if (granularityEl) {
    granularityEl.addEventListener('change', function () {
      if (!currentSession) return;
      api('sessions/' + currentSession.uuid + '/', {
        method: 'PATCH',
        body: JSON.stringify({
          action: 'set_granularity',
          granularity: granularityEl.value,
        }),
      }).then(renderView);
    });
  }

  renderQueue();
  syncQueueButtons();
})();
