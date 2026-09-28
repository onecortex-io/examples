/**
 * A recipe assistant: it finds recipes for the ingredients you have and respects
 * your diet. Built the way a Mastra agent is built, an Agent with a tool, and the
 * AI SDK's mock model in place of a real one.
 *
 * The mock streams its tool call in pieces and its answer word by word with a short
 * pause, so the chat looks the way it does with a real model. Recipes come from
 * recipes.json, so every answer is exact.
 *
 * What it shows:
 * - A tool call, `findRecipes`, whose input streams in pieces.
 * - What the caller sent, read by the tool from Mastra's request context: send
 *   `"diet": "vegan"` and only vegan recipes come back.
 */

import { Agent } from '@mastra/core/agent'
import { createTool } from '@mastra/core/tools'
import { simulateReadableStream } from 'ai'
import { MockLanguageModelV4 } from 'ai/test'
import { z } from 'zod'

import RECIPE_DATA from './recipes.json' with { type: 'json' }

interface Recipe {
  readonly name: string
  readonly minutes: number
  readonly ingredients: readonly string[]
  readonly diets: readonly string[]
}

const RECIPES: Recipe[] = RECIPE_DATA
const KNOWN = [...new Set(RECIPES.flatMap((recipe) => recipe.ingredients))]
const TOKEN_PAUSE_MS = 40

const usage = {
  inputTokens: { total: 1, noCache: 1, cacheRead: 0, cacheWrite: 0 },
  outputTokens: { total: 1, text: 1, reasoning: 0 },
}

interface PromptMessage {
  readonly role: string
  readonly content: unknown
}

function latestQuestion(prompt: readonly PromptMessage[]): string {
  const user = [...prompt].reverse().find((message) => message.role === 'user')
  const parts = Array.isArray(user?.content) ? (user.content as { text?: string }[]) : []
  return parts.map((part) => part.text ?? '').join('')
}

function toolOutput(prompt: readonly PromptMessage[]): { recipes: Recipe[]; diet: string | null } | undefined {
  const tool = [...prompt].reverse().find((message) => message.role === 'tool')
  if (!Array.isArray(tool?.content)) return undefined
  return (tool.content[0] as { output?: { value?: { recipes: Recipe[]; diet: string | null } } }).output?.value
}

function answer(found: { recipes: Recipe[]; diet: string | null }): string {
  if (found.recipes.length === 0) return 'I found no recipes for those ingredients. Try adding a staple like potatoes or tomatoes.'
  const list = found.recipes.map((recipe) => `${recipe.name} (${String(recipe.minutes)} minutes)`).join(' and ')
  return `You could make ${list}${found.diet === null ? '' : `, all ${found.diet}`}.`
}

function words(text: string, id: string) {
  return [
    { type: 'text-start' as const, id },
    ...text.split(' ').map((word, index) => ({ type: 'text-delta' as const, id, delta: index === 0 ? word : ` ${word}` })),
    { type: 'text-end' as const, id },
  ]
}

function turn(prompt: readonly PromptMessage[]) {
  const question = latestQuestion(prompt)
  if (question.trim().toLowerCase() === 'raise') throw new Error('the agent was asked to raise')
  const found = toolOutput(prompt)
  if (found !== undefined) {
    return [...words(answer(found), 'reply'), { type: 'finish' as const, finishReason: { unified: 'stop' as const, raw: 'stop' }, usage }]
  }
  const have = KNOWN.filter((ingredient) => question.toLowerCase().includes(ingredient))
  if (have.length === 0) {
    return [...words('Which ingredients do you have? For example: chickpeas and spinach.', 'ask'),
      { type: 'finish' as const, finishReason: { unified: 'stop' as const, raw: 'stop' }, usage }]
  }
  const input = JSON.stringify({ ingredients: have })
  return [
    { type: 'tool-input-start' as const, id: 'call_recipes', toolName: 'findRecipes' },
    { type: 'tool-input-delta' as const, id: 'call_recipes', delta: input.slice(0, 16) },
    { type: 'tool-input-delta' as const, id: 'call_recipes', delta: input.slice(16) },
    { type: 'tool-input-end' as const, id: 'call_recipes' },
    { type: 'tool-call' as const, toolCallId: 'call_recipes', toolName: 'findRecipes', input },
    { type: 'finish' as const, finishReason: { unified: 'tool-calls' as const, raw: 'tool_calls' }, usage },
  ]
}

const model = new MockLanguageModelV4({
  doStream: async ({ prompt }) => {
    await Promise.resolve()
    return { stream: simulateReadableStream({ chunks: turn(prompt as PromptMessage[]), chunkDelayInMs: TOKEN_PAUSE_MS }) }
  },
})

const findRecipes = createTool({
  id: 'findRecipes',
  description: 'Finds recipes that use the given ingredients, honouring the diet the caller asked for.',
  inputSchema: z.object({ ingredients: z.array(z.string()) }),
  execute: async ({ ingredients }, context) => {
    await Promise.resolve()
    const sent = context.requestContext?.get('onecortex') as { params?: { diet?: unknown } } | undefined
    const diet = typeof sent?.params?.diet === 'string' ? sent.params.diet : null
    const recipes = RECIPES
      .filter((recipe) => ingredients.every((ingredient) => recipe.ingredients.includes(ingredient)))
      .filter((recipe) => diet === null || recipe.diets.includes(diet))
    return { recipes, diet }
  },
})

export const agent = new Agent({
  id: 'recipe-assistant',
  name: 'Recipe assistant',
  instructions: 'Find recipes with findRecipes for the ingredients the user has, and list them.',
  model,
  tools: { findRecipes },
})
