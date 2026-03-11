"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { chatApi, Conversation, Message } from "@/lib/api";
import { Send, Plus, LogOut, MessageSquare } from "lucide-react";

export default function ChatPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [studentName, setStudentName] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // 初始化：读取 token
  useEffect(() => {
    const t = localStorage.getItem("session_token");
    const n = localStorage.getItem("student_name");
    if (!t) { router.push("/parent/login"); return; }
    setToken(t);
    setStudentName(n ?? "");
  }, [router]);

  // 加载历史对话列表
  const loadConversations = useCallback(async (t: string) => {
    try {
      const list = await chatApi.getConversations(t);
      setConversations(list);
      if (list.length > 0) selectConversation(list[0].id, t);
    } catch { router.push("/parent/login"); }
  }, [router]);

  useEffect(() => {
    if (token) loadConversations(token);
  }, [token, loadConversations]);

  // 滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function selectConversation(id: number, t?: string) {
    const tk = t ?? token;
    setActiveId(id);
    try {
      const conv = await chatApi.getConversation(tk, id);
      setMessages(conv.messages);
    } catch { console.error("加载对话失败"); }
  }

  async function handleNewConversation() {
    try {
      const conv = await chatApi.newConversation(token);
      setConversations((prev) => [conv, ...prev]);
      setActiveId(conv.id);
      setMessages([]);
    } catch (e: unknown) { alert(e instanceof Error ? e.message : "创建失败"); }
  }

  async function handleSend() {
    if (!input.trim() || !activeId || sending) return;
    const content = input.trim();
    setInput("");
    setSending(true);

    // 乐观更新：先显示用户消息
    const tmpMsg: Message = { id: Date.now(), role: "user", content, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, tmpMsg]);

    try {
      const res = await chatApi.sendMessage(token, activeId, content);
      const aiMsg: Message = { id: res.message_id, role: "assistant", content: res.content, created_at: new Date().toISOString() };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: unknown) {
      setMessages((prev) => prev.filter((m) => m.id !== tmpMsg.id));
      alert(e instanceof Error ? e.message : "发送失败");
    } finally {
      setSending(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("session_token");
    localStorage.removeItem("student_name");
    router.push("/parent/login");
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }

  const SUGGESTIONS = [
    "孩子这周的整体表现怎么样？",
    "最近的考试成绩有什么变化趋势？",
    "作业完成情况如何？",
    "针对孩子目前的情况，有什么提升建议？",
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧：对话历史列表 */}
      <aside className="w-56 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <p className="text-xs text-gray-400 mb-0.5">当前学生</p>
          <p className="font-semibold text-gray-900 truncate">{studentName}</p>
        </div>

        <div className="p-2">
          <button onClick={handleNewConversation}
            className="flex items-center gap-2 w-full text-sm text-blue-600 hover:bg-blue-50 rounded-lg px-3 py-2 transition-colors">
            <Plus size={15} /> 新建对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {conversations.map((c) => (
            <button key={c.id} onClick={() => selectConversation(c.id)}
              className={`flex items-center gap-2 w-full text-left text-sm rounded-lg px-3 py-2 transition-colors ${
                activeId === c.id ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:bg-gray-100"
              }`}>
              <MessageSquare size={14} className="shrink-0" />
              <span className="truncate">
                {new Date(c.created_at).toLocaleDateString("zh-CN", { month: "short", day: "numeric" })} 的对话
              </span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="text-xs text-gray-400 px-3 py-2">暂无对话记录</p>
          )}
        </div>

        <div className="p-2 border-t">
          <button onClick={handleLogout}
            className="flex items-center gap-2 w-full text-sm text-gray-500 hover:bg-gray-100 rounded-lg px-3 py-2">
            <LogOut size={14} /> 退出登录
          </button>
        </div>
      </aside>

      {/* 右侧：对话区 */}
      <div className="flex-1 flex flex-col">
        {/* 顶栏 */}
        <header className="bg-white border-b px-6 py-3 flex items-center">
          <h1 className="font-semibold text-gray-900">学情 AI 助手</h1>
          <span className="ml-2 text-xs text-gray-400">随时了解孩子的学习情况</span>
        </header>

        {/* 消息区 */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && activeId && (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-6">你好！有什么想了解的吗？</p>
              <div className="grid grid-cols-2 gap-2 max-w-lg mx-auto">
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => { setInput(s); }}
                    className="text-left text-sm bg-white border rounded-xl px-4 py-3 text-gray-600 hover:border-blue-300 hover:text-blue-700 transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.length === 0 && !activeId && (
            <div className="text-center py-12 text-gray-400">
              <MessageSquare size={40} className="mx-auto mb-3 opacity-30" />
              <p>点击左侧「新建对话」开始</p>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs shrink-0 mr-2 mt-1">
                  AI
                </div>
              )}
              <div className={`max-w-lg ${m.role === "user" ? "order-first" : ""}`}>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-white border text-gray-800 rounded-bl-sm shadow-sm"
                }`}>
                  {m.content}
                </div>
                <p className={`text-xs text-gray-400 mt-1 ${m.role === "user" ? "text-right" : ""}`}>
                  {formatTime(m.created_at)}
                </p>
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs shrink-0 mr-2">
                AI
              </div>
              <div className="bg-white border rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* 输入栏 */}
        <div className="bg-white border-t px-6 py-4">
          <div className="flex gap-3 items-end max-w-3xl mx-auto">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder={activeId ? "输入问题，Enter 发送，Shift+Enter 换行" : "请先新建对话"}
              disabled={!activeId}
              rows={1}
              className="flex-1 border rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-50 disabled:cursor-not-allowed"
              style={{ maxHeight: "120px" }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !activeId || sending}
              className="bg-blue-600 text-white p-2.5 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
