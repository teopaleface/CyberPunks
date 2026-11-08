/** Rulează cu același mediu privat ca Next. Nu afișează parole sau tokenuri. */
const base = process.env.DAYBREAK_WEB_ORIGIN ?? "http://127.0.0.1:3870";
if (!process.env.DAYBREAK_INTERNAL_TOKEN)
  throw new Error("Load the private runtime environment first.");
const response = await fetch(`${base}/api/dev/provision-demo`, {
  method: "POST",
  headers: {
    origin: base,
    authorization: `Bearer ${process.env.DAYBREAK_INTERNAL_TOKEN}`,
  },
});
const data = await response.json();
if (!response.ok) {
  console.error(data.error ?? "Provisioning failed.");
  process.exitCode = 1;
} else console.log(JSON.stringify(data, null, 2));
export {};
