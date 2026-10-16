export default {
  async fetch(request, env, ctx) {
    if (request.method === "GET") {
      return new Response("ok - cloudflare worker alive", { status: 200 });
    }

    if (request.method !== "POST") {
      return new Response("not found", { status: 404 });
    }

    // 1. Проверка секрета Telegram
    if (env.TG_SECRET) {
      const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (got !== env.TG_SECRET) {
        return new Response("unauthorized", { status: 401 });
      }
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("ok - bad json", { status: 200 });
    }

    // Не ждём отправку сообщения — отвечаем Telegram 200 сразу
    ctx.waitUntil(handleUpdate(update, env));

    return new Response("ok", { status: 200 });
  },
};

async function handleUpdate(update, env) {
  const message = update.message || update.edited_message || {};
  const chatId = message.chat?.id;
  const text = message.text || "";
  if (!chatId) return;

  let reply;
  if (text === "/start") reply = "Привет! Я бот на Cloudflare Workers 👋\nПопробуй /ping";
  else if (text === "/ping") reply = "pong 🏓";
  else if (text.startsWith("/echo ")) reply = text.slice(6);
  else reply = `Ты написал: ${text}`;

  await tgApi(env, "sendMessage", { chat_id: chatId, text: reply });
}

async function tgApi(env, method, payload) {
  if (!env.TG_TOKEN) {
    console.log("ERROR: TG_TOKEN is not set");
    return;
  }
  try {
    const r = await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/${method}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    console.log(`TG ${method}: ${r.status}`);
  } catch (e) {
    console.log(`TG ${method} failed: ${e}`);
  }
}
