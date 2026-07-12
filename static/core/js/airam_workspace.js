(function () {
  var storageKey = 'airam_workspace_id';
  var panel = document.getElementById('airam-workspace-panel');
  if (!panel) return;

  var bodyEl = panel.querySelector('[data-workspace-body]');
  var frameEl = panel.querySelector('[data-workspace-frame]');
  var countEl = panel.querySelector('[data-workspace-count]');
  var projectEl = panel.querySelector('[data-workspace-project]');
  var projectSelect = panel.querySelector('[data-workspace-project-select]');
  var toggleBtn = panel.querySelector('[data-workspace-action="toggle"]');
  var current = null;

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
          if (!r.ok) throw new Error(data.error || 'Error AIRAM workspace');
          return data;
        });
      });
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function siteRoot() {
    var link = document.querySelector('nav.breadcrumb a');
    if (!link) return '/';
    var href = link.getAttribute('href') || '/';
    var idx = href.indexOf('biblioteca/');
    return idx >= 0 ? href.slice(0, idx) : '/';
  }

  function saveLocal(uuid) {
    if (uuid) localStorage.setItem(storageKey, uuid);
  }

  function getLocal() {
    return localStorage.getItem(storageKey);
  }

  function render(data) {
    current = data;
    if (!data || !data.uuid) {
      panel.hidden = true;
      return;
    }
    panel.hidden = false;
    var frame = data.frame || [];
    countEl.textContent = String(frame.length);
    if (projectEl) {
      if (data.project_title) {
        projectEl.hidden = false;
        projectEl.textContent = 'Cuaderno: ' + data.project_title;
      } else {
        projectEl.hidden = true;
        projectEl.textContent = '';
      }
    }
    if (!frame.length) {
      frameEl.innerHTML = '<li class="airam-workspace__empty">Visita temas en distintas taxonomías para construir tu marco.</li>';
    } else {
      frameEl.innerHTML = frame.map(function (item) {
        var url = siteRoot() + 'biblioteca/temas/' + item.concept_uuid + '/';
        return '<li class="airam-workspace__item">' +
          '<a href="' + escapeHtml(url) + '" class="airam-workspace__link">' + escapeHtml(item.label || item.concept_uuid) + '</a>' +
          '<span class="airam-workspace__weight" title="Peso">' + item.weight + '</span>' +
          '</li>';
      }).join('');
    }
    var promoteBtn = panel.querySelector('[data-workspace-action="promote"]');
    if (promoteBtn) {
      promoteBtn.disabled = !(data.project_uuid && frame.length);
    }
    saveLocal(data.uuid);
  }

  function ensureWorkspace() {
    var localId = getLocal();
    if (localId) {
      return api('workspace/' + localId + '/').then(render).catch(function () {
        localStorage.removeItem(storageKey);
        return api('workspace/', { method: 'POST', body: '{}' }).then(render);
      });
    }
    return api('workspace/', { method: 'POST', body: '{}' }).then(render);
  }

  function recordConcept(conceptUuid, eventType) {
    if (!conceptUuid) return Promise.resolve();
    return ensureWorkspace().then(function () {
      if (!current || !current.uuid) return;
      return api('workspace/' + current.uuid + '/', {
        method: 'PATCH',
        body: JSON.stringify({
          action: 'record_concept',
          concept_uuid: conceptUuid,
          event_type: eventType || 'visited',
        }),
      }).then(render);
    }).catch(function () {});
  }

  function loadProjects() {
    if (!projectSelect) return Promise.resolve();
    return api('workspace/projects/').then(function (data) {
      var options = '<option value="">— Sin vincular —</option>';
      (data.projects || []).forEach(function (p) {
        options += '<option value="' + escapeHtml(p.uuid) + '">' + escapeHtml(p.title) + '</option>';
      });
      projectSelect.innerHTML = options;
      if (current && current.project_uuid) {
        projectSelect.value = current.project_uuid;
      }
    }).catch(function () {});
  }

  function linkProject() {
    if (!current || !projectSelect) return;
    var pid = projectSelect.value;
    if (!pid) return;
    api('workspace/' + current.uuid + '/', {
      method: 'PATCH',
      body: JSON.stringify({ action: 'link_project', project_uuid: pid }),
    }).then(render);
  }

  function promoteMarkers() {
    if (!current) return;
    api('workspace/' + current.uuid + '/', {
      method: 'PATCH',
      body: JSON.stringify({ action: 'promote_markers', min_weight: 3 }),
    }).then(function () {
      alert('Conceptos promovidos a marcadores del cuaderno (si superaban el umbral).');
    });
  }

  function resetWorkspace() {
    localStorage.removeItem(storageKey);
    api('workspace/', { method: 'POST', body: JSON.stringify({ force_new: true }) }).then(render);
  }

  panel.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-workspace-action]');
    if (!btn) return;
    var action = btn.getAttribute('data-workspace-action');
    if (action === 'toggle' && bodyEl) {
      var open = bodyEl.hidden;
      bodyEl.hidden = !open;
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    } else if (action === 'link-project') {
      linkProject();
    } else if (action === 'promote') {
      promoteMarkers();
    } else if (action === 'reset') {
      resetWorkspace();
    }
  });

  var topicScript = document.querySelector('script[data-topic-uuid]');
  if (topicScript) {
    recordConcept(topicScript.getAttribute('data-topic-uuid'), 'visited');
  } else {
    ensureWorkspace().then(render);
  }
  loadProjects();

  window.AIRAM_WORKSPACE = {
    recordConcept: recordConcept,
    refresh: function () { return ensureWorkspace().then(render); },
  };
})();
