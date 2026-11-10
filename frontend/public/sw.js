/* BrandVault service worker: shows push notifications, even when the app tab is closed. */
self.addEventListener("push", (event) => {
  let data = { title: "BrandVault", body: "", link: "/dashboard" };
  try { data = { ...data, ...event.data.json() }; } catch (e) { /* plain or empty payload */ }
  event.waitUntil(self.registration.showNotification(data.title, {
    body: data.body,
    icon: "/bv-icon.png",
    badge: "/bv-icon.png",
    data: { link: data.link },
    tag: data.link,
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const link = (event.notification.data && event.notification.data.link) || "/dashboard";
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const c of all) {
      if ("focus" in c) { await c.navigate(link).catch(() => {}); return c.focus(); }
    }
    return self.clients.openWindow(link);
  })());
});
