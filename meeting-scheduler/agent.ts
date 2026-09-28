/**
 * A meeting scheduler: it checks your calendar for the day you ask about, holds
 * the first free slot and tells you. Built the way an AI SDK agent is built, a
 * ToolLoopAgent with two tools, and the SDK's mock model in place of a real one.
 *
 * The mock plans the way a model does, one tool per turn: check the calendar, then
 * hold a slot, then answer. It streams each tool's input in pieces and the answer
 * word by word. The calendar is calendar.json and busy.json, so every answer is
 * exact.
 *
 * What it shows:
 * - A multi-turn tool loop: two tool calls in one run, each with its result.
 * - A tool that fails for a weekend, reported as an error result, and the agent
 *   recovering from it.
 * The AI SDK has no per call slot for what the caller sent, so this agent reads
 * none; an agent that needs it is a plain function taking `request`.
 */

import { ToolLoopAgent, simulateReadableStream, tool } from 'ai'
import { MockLanguageModelV4 } from 'ai/test'
import { z } from 'zod'

import BUSY_DATA from './busy.json' with { type: 'json' }
import HOURS_DATA from './calendar.json' with { type: 'json' }

const HOURS: Record<string, string[]> = HOURS_DATA
const BUSY: Record<string, string[]> = BUSY_DATA
const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const TOKEN_PAUSE_MS = 40

const usage = {
  inputTokens: { total: 1, noCache: 1, cacheRead: 0, cacheWrite: 0 },
  outputTokens: { total: 1, text: 1, reasoning: 0 },
}

interface PromptMessage {
  readonly role: string
  readonly content: unknown
}

interface ToolPart {
  readonly toolName: string
  readonly output: { readonly type: string; readonly value: unknown }
}

const capital = (day: string) => day.charAt(0).toUpperCase() + day.slice(1)

function results(prompt: readonly PromptMessage[]): ToolPart[] {
  return prompt.filter((m) => m.role === 'tool').flatMap((m) => (Array.isArray(m.content) ? (m.content as ToolPart[]) : []))
}

function question(prompt: readonly PromptMessage[]): string {
  const user = [...prompt].reverse().find((m) => m.role === 'user')
  return (Array.isArray(user?.content) ? (user.content as { text?: string }[]) : []).map((p) => p.text ?? '').join('')
}

const stop = { type: 'finish' as const, finishReason: { unified: 'stop' as const, raw: 'stop' }, usage }
const toolsNext = { type: 'finish' as const, finishReason: { unified: 'tool-calls' as const, raw: 'tool_calls' }, usage }

function say(text: string) {
  return [
    { type: 'text-start' as const, id: 'reply' },
    ...text.split(' ').map((word, i) => ({ type: 'text-delta' as const, id: 'reply', delta: i === 0 ? word : ` ${word}` })),
    { type: 'text-end' as const, id: 'reply' },
    stop,
  ]
}

function call(id: string, toolName: string, input: object) {
  const json = JSON.stringify(input)
  return [
    { type: 'tool-input-start' as const, id, toolName },
    { type: 'tool-input-delta' as const, id, delta: json.slice(0, 8) },
    { type: 'tool-input-delta' as const, id, delta: json.slice(8) },
    { type: 'tool-input-end' as const, id },
    { type: 'tool-call' as const, toolCallId: id, toolName, input: json },
    toolsNext,
  ]
}

function turn(prompt: readonly PromptMessage[]) {
  const asked = question(prompt).toLowerCase()
  if (asked.trim() === 'raise') throw new Error('the agent was asked to raise')
  const day = DAYS.find((d) => asked.includes(d))
  if (day === undefined) return say('Which day should I look at? For example: Thursday.')
  const done = results(prompt)
  const checked = done.find((r) => r.toolName === 'checkCalendar')
  const held = done.find((r) => r.toolName === 'holdSlot')
  if (checked === undefined) return call('call_check', 'checkCalendar', { day })
  if (checked.output.type !== 'json') return say(`I can only schedule meetings on weekdays. ${capital(day)} is not one; try Monday to Friday.`)
  const free = (checked.output.value as { free: string[] }).free
  if (free.length === 0) return say(`${capital(day)} is fully booked. Try another day.`)
  if (held === undefined) return call('call_hold', 'holdSlot', { day, time: free[0] })
  const slot = held.output.value as { day: string; time: string }
  return say(`I have held ${capital(slot.day)} at ${slot.time} for you. It is the first free hour that day.`)
}

const model = new MockLanguageModelV4({
  doStream: async ({ prompt }) => {
    await Promise.resolve()
    return { stream: simulateReadableStream({ chunks: turn(prompt as PromptMessage[]), chunkDelayInMs: TOKEN_PAUSE_MS }) }
  },
})

export const checkCalendar = tool({
  description: 'Lists the free hours on a weekday.',
  inputSchema: z.object({ day: z.string() }),
  execute: ({ day }) => {
    const hours = HOURS[day]
    if (hours === undefined) throw new Error(`${capital(day)} is not a working day.`)
    return { day, free: hours.filter((hour) => !(BUSY[day] ?? []).includes(hour)) }
  },
})

export const holdSlot = tool({
  description: 'Holds an hour on the calendar.',
  inputSchema: z.object({ day: z.string(), time: z.string() }),
  execute: ({ day, time }) => ({ day, time, held: true }),
})

export const agent = new ToolLoopAgent({
  model,
  instructions: 'Check the calendar, hold the first free hour, and confirm it.',
  tools: { checkCalendar, holdSlot },
})
