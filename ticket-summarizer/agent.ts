/**
 * A support ticket summariser: it classifies the ticket, looks up the customer
 * and writes a one line summary for the team that picks it up. Built the way a
 * LangChain.js chain is built, a runnable calling tools, with no model: the
 * classification is keyword rules, which is what a first version often is.
 *
 * What it shows:
 * - Two tool calls, `classify_ticket` and `lookup_customer`, with their results.
 * - A tool that fails for an unknown customer, reported as an error result, while
 *   the chain carries on without the customer's details.
 * - What the caller sent, read from `config.configurable.onecortex`: send
 *   `"team": "Mobile"` and the ticket is routed there.
 *
 * The chain takes the ticket as a bare string, which is how the platform invokes
 * a LangChain runnable.
 */

import { RunnableLambda, type RunnableConfig } from '@langchain/core/runnables'
import { tool } from '@langchain/core/tools'
import { z } from 'zod'

import CUSTOMER_DATA from './customers.json' with { type: 'json' }

interface Customer {
  readonly name: string
  readonly plan: string
}

const CUSTOMERS: Record<string, Customer> = CUSTOMER_DATA

const classifyTicket = tool(({ text }) => {
  const lower = text.toLowerCase()
  const category = /crash|error|broken|bug/.test(lower) ? 'bug' : /invoice|charge|refund|bill/.test(lower) ? 'billing' : 'question'
  const priority = /crash|down|cannot|can't|urgent/.test(lower) ? 'high' : 'normal'
  return JSON.stringify({ category, priority })
}, {
  name: 'classify_ticket',
  description: 'Classifies a support ticket by category and priority.',
  schema: z.object({ text: z.string() }),
})

const lookupCustomer = tool(({ id }) => {
  const customer = CUSTOMERS[id]
  if (customer === undefined) throw new Error(`No customer ${id} exists.`)
  return JSON.stringify(customer)
}, {
  name: 'lookup_customer',
  description: 'Looks up a customer by account id.',
  schema: z.object({ id: z.string() }),
})

export const chain = RunnableLambda.from(async (input: string, config?: RunnableConfig) => {
  if (input.trim().toLowerCase() === 'raise') throw new Error('the agent was asked to raise')
  const sent = config?.configurable?.['onecortex'] as { params?: { team?: unknown } } | undefined
  const team = typeof sent?.params?.team === 'string' ? sent.params.team : 'Support'

  const ticket = input.replace(/^summari[sz]e this ticket:\s*/i, '')
  const { category, priority } = JSON.parse(String(await classifyTicket.invoke({ text: ticket }, config))) as { category: string; priority: string }

  const id = /\b([A-Z]+-\d+)\b/.exec(ticket)?.[1]
  let who = 'an unknown customer'
  if (id !== undefined) {
    try {
      const customer = JSON.parse(String(await lookupCustomer.invoke({ id }, config))) as Customer
      who = `${customer.name} (${customer.plan})`
    } catch {
      who = `customer ${id}, who is not on record`
    }
  }

  const issue = (ticket.split(/(?<=\.)\s/)[0] ?? ticket).replace(/\.$/, '')
  const level = priority === 'high' ? 'High priority' : 'Normal priority'
  return `${level} ${category} from ${who}: ${issue}. Routed to ${team}.`
})
