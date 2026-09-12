"use strict";
(() => {
  const data = JSON.parse(document.getElementById("workbench-data").textContent);
  const items = data.items;
  const $ = id => document.getElementById(id);
  const byId = new Map(items.map(item => [item.id, item]));
  const byUrl = new Map(items.filter(item => item.url).map(item => [canonicalUrl(item.url), item]));
  const labels = {now: "准备做和正在推进的事项。状态来自 Linear；是否完成请看具体成果。", ideas: "还未安排或需要进一步讨论的事项。先看想解决什么问题。", review: "Linear 中标为 In Review 的事项。打开后查看成果和待判断的问题。", knowledge: "团队文档、事项文档与已登记的本地材料，都在这个目录里。", all: "所有已读取的事项和材料，包括已结束的事项。"};
  const kindLabels = {issue: "事项", document: "Linear 文档", knowledge: "知识", code: "代码入口", guide: "使用说明"};
  let state = {view: "now", q: "", domain: "", kind: "", item: ""};
  let active = null;
  let visible = [];

  function canonicalUrl(value) {
    try {
      const url = new URL(value);
      const parts = url.pathname.split("/").filter(Boolean);
      if (url.hostname === "linear.app" && parts.length >= 3) {
        if (parts[1] === "issue") return "https://linear.app/" + parts.slice(0,3).join("/");
        const slug = parts[2].match(/([a-f0-9]{12})$/)?.[1];
        if (parts[1] === "document" && slug) return "https://linear.app/" + parts[0] + "/document/" + slug;
      }
      return url.origin + url.pathname.replace(/\/$/, "");
    } catch {return value;}
  }
  function dateLabel(value, full = true) {
    if (!value) return "未提供";
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return value;
    return new Intl.DateTimeFormat("zh-CN", {year:"numeric",month:"2-digit",day:"2-digit",...(full ? {hour:"2-digit",minute:"2-digit",timeZoneName:"short"} : {})}).format(date);
  }
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function itemHash(item, view) {
    return "#" + new URLSearchParams({view: view || (item.group === "closed" ? "all" : item.group), item: item.id}).toString();
  }
  function syncHash(push = false) {
    const params = new URLSearchParams();
    for (const key of ["view", "q", "domain", "kind", "item"]) if (state[key]) params.set(key, state[key]);
    const hash = "#" + params.toString();
    // file:// history changes are allowed in modern browsers, with a hash-only fallback.
    try {history[push ? "pushState" : "replaceState"](null, "", hash);} catch {location.hash = hash;}
  }
  function fromHash() {
    const params = new URLSearchParams(location.hash.slice(1));
    state = {view: labels[params.get("view")] ? params.get("view") : "now", q: params.get("q") || "", domain: params.get("domain") || "", kind: params.get("kind") || "", item: params.get("item") || ""};
    $("search").value = state.q;
    $("domain").value = state.domain;
    $("kind").value = state.kind;
    render();
  }
  function matches(item) {
    if (state.view !== "all" && item.group !== state.view) return false;
    if (state.domain && item.domain !== state.domain) return false;
    if (state.kind && (state.kind === "local" ? !item.id.startsWith("local:") : item.kind !== state.kind)) return false;
    const haystack = [item.title, item.identifier, item.body, item.domain, item.path, item.parent].join("\n").toLocaleLowerCase();
    return state.q.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean).every(term => haystack.includes(term));
  }
  function excerpt(item) {
    let text = item.body.replace(/^---\r?\n[\s\S]*?\r?\n(?:---|\.\.\.)\s*\r?\n/, "").replace(/[#*`>|]/g," ").replace(/\[([^\]]+)\]\([^)]*\)/g,"$1").replace(/\s+/g," ").trim();
    const query = state.q.trim().split(/\s+/)[0];
    const at = query ? text.toLocaleLowerCase().indexOf(query.toLocaleLowerCase()) : -1;
    if (at > 35) text = "…" + text.slice(at - 25);
    return text.slice(0, 160);
  }
  function render() {
    document.querySelectorAll("[data-view]").forEach(button => {
      const view = button.dataset.view;
      button.setAttribute("aria-pressed", String(view === state.view));
      button.querySelector("span").textContent = items.filter(item => view === "all" || item.group === view).length;
    });
    $("view-description").textContent = labels[state.view];
    visible = items.filter(matches);
    $("result-count").textContent = visible.length + " 条";
    $("items").replaceChildren();
    $("empty-list").hidden = visible.length > 0;
    const selected = visible.find(item => item.id === state.item);
    // A bookmarked record remains readable even when another filter hides it.
    active = selected || (state.item && byId.get(state.item)) || visible[0] || null;
    if (!visible.length && !state.item) active = null;
    if (active) state.item = active.id;
    for (const item of visible) {
      const li = element("li");
      const button = element("button", "item-button");
      button.dataset.item = item.id;
      button.setAttribute("aria-current", String(item.id === active?.id));
      const top = element("span", "item-top");
      top.append(element("span", "item-id", item.identifier || kindLabels[item.kind] || "材料"), element("span", "item-status", item.status));
      const foot = element("span", "item-foot");
      foot.append(element("span", "item-domain", item.domain), element("span", "", dateLabel(item.updatedAt, false)));
      button.append(top, element("span", "item-title", item.title), element("span", "item-excerpt", excerpt(item)), foot);
      button.addEventListener("click", () => {state.item = item.id; render(); syncHash(true); document.querySelector(".workspace").classList.add("show-detail"); $("reading").scrollTop = 0; $("reading").focus({preventScroll:true}); if (matchMedia("(max-width:620px)").matches) $("reading").scrollIntoView({block:"start"});});
      li.append(button); $("items").append(li);
    }
    renderDetail();
  }
  function renderDetail() {
    $("detail").hidden = !active;
    $("empty-detail").hidden = !!active;
    if (!active) return;
    $("detail-title").textContent = active.title;
    $("detail-labels").replaceChildren(...[active.identifier || kindLabels[active.kind] || "材料", active.status, active.domain].map(text => element("span", "", text)));
    $("detail-meta").replaceChildren();
    const facts = ["来源：" + active.source, "正文更新：" + dateLabel(active.updatedAt)];
    if (active.capturedAt) facts.push("本地快照保存：" + dateLabel(active.capturedAt));
    if (active.inspectedAt) facts.push("入口核对：" + dateLabel(active.inspectedAt));
    if (active.parent) facts.push("归属：" + active.parent);
    for (const text of facts) $("detail-meta").append(element("span", "", text));
    const source = $("open-source");
    source.hidden = !active.url && !active.localUrl;
    if (active.url || active.localUrl) {source.href = active.url || active.localUrl; source.textContent = active.url?.includes("linear.app/") ? "去 Linear 继续 ↗" : active.localUrl ? "打开仓库文件 ↗" : "打开来源 ↗";}
    $("body").innerHTML = active.html; // Generated by html-disabled MarkdownIt and restricted URL rendering.
    $("body").querySelectorAll("a[href]").forEach(link => {
      if (link.getAttribute("href").startsWith("#reader-")) {
        link.addEventListener("click", event => {event.preventDefault(); document.getElementById(decodeURIComponent(link.hash.slice(1)))?.scrollIntoView({block:"start"});});
        return;
      }
      const linked = byUrl.get(canonicalUrl(link.getAttribute("href")));
      if (linked) {link.href = itemHash(linked); link.removeAttribute("target"); link.title = "在本页阅读：" + linked.title;}
    });
    $("source-note").replaceChildren(element("p", "", active.authority));
    if (active.path) $("source-note").append(element("p", "", "仓库入口：" + active.path));
    if (active.source === "Linear") $("source-note").append(element("p", "", "此处保留读取时的全文。继续工作前，请让 AI 重新读取线上事项和必要文档。"));
    const bodyReferences = new Set([...$("body").querySelectorAll("a[href^='#']")].map(link => new URLSearchParams(link.hash.slice(1)).get("item")));
    const related = items.filter(item => item.id !== active.id && (bodyReferences.has(item.id) || (item.identifier && active.relatedIssues.includes(item.identifier)) || (active.identifier && item.parent === active.identifier) || (active.documentIds || []).includes(item.nativeId)));
    $("related").hidden = !related.length;
    $("related").replaceChildren(element("span", "", "关联阅读"));
    related.forEach(item => {const link = element("a", "", item.identifier || item.title); link.href = itemHash(item); link.title = item.title; $("related").append(link);});
  }
  function changeFilter() {
    state.q = $("search").value; state.domain = $("domain").value; state.kind = $("kind").value;
    state.item = ""; render(); syncHash();
    document.querySelector(".workspace").classList.remove("show-detail");
  }
  const saves = items.map(item => item.capturedAt).filter(Boolean).sort();
  $("snapshot-time").textContent = saves.length ? "快照最近保存 " + dateLabel(saves.at(-1)) : "尚未读取 Linear 快照";
  for (const domain of [...new Set(items.map(item => item.domain))].sort()) {
    const option = element("option", "", domain); option.value = domain; $("domain").append(option);
  }
  document.querySelector("form").addEventListener("submit", event => event.preventDefault());
  $("search").addEventListener("input", () => {state.view = "all"; changeFilter();});
  $("domain").addEventListener("change", changeFilter);
  $("kind").addEventListener("change", changeFilter);
  document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => {state.view = button.dataset.view; state.item = ""; state.kind = ""; $("kind").value = ""; render(); syncHash(true); document.querySelector(".workspace").classList.remove("show-detail");}));
  $("clear-filters").addEventListener("click", () => {$("search").value = ""; $("domain").value = ""; $("kind").value = ""; state.view = "all"; changeFilter(); $("search").focus();});
  $("back-to-list").addEventListener("click", () => {document.querySelector(".workspace").classList.remove("show-detail"); document.querySelector('.item-button[aria-current="true"]')?.focus({preventScroll:true});});
  $("handoff").addEventListener("click", () => {
    if (!active) return;
    const source = active.url || "仓库文件 " + active.path;
    $("handoff-text").value = active.kind === "issue"
      ? "请继续推进 " + (active.identifier || active.title) + "（" + source + "）。\n\n先重新读取线上事项的完整正文、必要评论和关联文档，说明我想达成什么、已有结果、还缺什么。按已有授权完成下一步，把可阅读的结果、证据和下一动作写回原事项；需要调整目标时先把具体问题说清楚。\n\n这次我希望：请判断最有价值的下一步并推进。"
      : "请先阅读《" + active.title + "》（" + source + "），并核对适用范围和更新时间。" + (active.path ? "\n本地入口：" + active.path : "") + "\n\n这次我希望：请基于这份材料继续讨论或处理工作。如果需要跟踪，先查已有事项并关联；不必为了读材料新建事项。";
    $("copy-status").textContent = "";
    $("handoff-dialog").showModal();
    $("handoff-text").focus();
  });
  $("close-handoff").addEventListener("click", () => $("handoff-dialog").close());
  $("copy-handoff").addEventListener("click", async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText($("handoff-text").value);
      $("copy-status").textContent = "已复制，可以粘贴到会话中。";
    } catch {
      $("handoff-text").focus(); $("handoff-text").select();
      $("copy-status").textContent = "浏览器不允许直接复制，内容已选中，请按 Ctrl/Cmd+C。";
    }
  });
  document.addEventListener("keydown", event => {
    const editing = event.target.matches("input,textarea,select,[contenteditable]");
    if (event.key === "/" && !editing && !$("handoff-dialog").open && !event.ctrlKey && !event.metaKey) {event.preventDefault(); $("search").focus();}
  });
  window.addEventListener("popstate", fromHash);
  window.addEventListener("hashchange", () => {fromHash(); if (state.item) document.querySelector(".workspace").classList.add("show-detail");});
  fromHash();
  if (location.hash && state.item) document.querySelector(".workspace").classList.add("show-detail");
})();
