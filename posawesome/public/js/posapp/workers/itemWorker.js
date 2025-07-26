importScripts("https://unpkg.com/dexie@latest/dist/dexie.min.js");

const db = new Dexie("posawesome_offline");
db.version(1).stores({ keyval: "&key" });

async function persist(key, value) {
	try {
		await db.table("keyval").put({ key, value });
	} catch (e) {
		console.error("Worker persist failed", e);
	}
	if (typeof localStorage !== "undefined") {
		try {
			localStorage.setItem(`posa_${key}`, JSON.stringify(value));
		} catch (err) {
			console.error("Worker localStorage failed", err);
		}
	}
}

self.onmessage = async (event) => {
	//console.log("item worker", event);
	const data = event.data || {};
	if (data.type === "parse_and_cache") {
		try {
			const parsed = JSON.parse(data.json);
			const items = parsed.message || parsed;
			let cache = {};
			try {
				const stored = await db.table("keyval").get("price_list_cache");
				if (stored && stored.value) cache = stored.value;
			} catch (e) {
				console.error("Failed to read cache in worker", e);
			}
			cache[data.priceList] = { items, timestamp: Date.now() };
			await persist("price_list_cache", cache);
			self.postMessage({ type: "parsed", items });
		} catch (err) {
			console.log(err);
			self.postMessage({ type: "error", error: err.message });
		}
	} else if (data.type === "persist") {
		await persist(data.key, data.value);
		self.postMessage({ type: "persisted", key: data.key });
	}
};
