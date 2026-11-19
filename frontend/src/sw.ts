/// <reference lib="webworker" />
import { clientsClaim } from "workbox-core";
import { cleanupOutdatedCaches, createHandlerBoundToURL, precacheAndRoute } from "workbox-precaching";
import { NavigationRoute, registerRoute } from "workbox-routing";
import { NetworkOnly } from "workbox-strategies";

declare let self: ServiceWorkerGlobalScope;

self.skipWaiting();
clientsClaim();

cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST);

const navigationHandler = createHandlerBoundToURL("/index.html");
const navigationRoute = new NavigationRoute(navigationHandler, {
  denylist: [/^\/api\//, /^\/health$/],
});
registerRoute(navigationRoute);

registerRoute(
  ({ url }) => url.pathname.startsWith("/api/") || url.pathname === "/health",
  new NetworkOnly()
);
