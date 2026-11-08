import { describe, expect, test } from "bun:test";
import { conversationHistory } from "./history";
import type { Message } from "./types";

describe("conversation history sent through text and voice", () => {
  test("the eighth exchange sends only the latest twelve messages", () => {
    const messages: Message[] = Array.from({ length: 14 }, (_, i) => ({
      role: i % 2 ? "assistant" : "user",
      content: `message ${i}`,
    }));
    const history = conversationHistory(messages);
    expect(history).toHaveLength(12);
    expect(history[0].content).toBe("message 2");
    expect(history.at(-1)?.content).toBe("message 13");
    expect(messages).toHaveLength(14);
  });

  test("a maximum-size current message can remain in the next request's history", () => {
    const content = "a".repeat(4000);
    expect(conversationHistory([{ role: "user", content }])).toEqual([{ role: "user", content }]);
  });

  test("oversize historical context cannot exceed the API contract", () => {
    expect(conversationHistory([{ role: "assistant", content: "x".repeat(5000) }])[0].content.length).toBe(4000);
  });
});
