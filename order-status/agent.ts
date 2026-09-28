/**
 * An order status assistant, written as a plain exported function: no framework.
 *
 * It finds the order number in the question, looks the order up with a tool of
 * its own, and answers from what the tool returned. The tool and its result are
 * yielded as plain objects, which the platform reports as a tool call on every
 * surface, and the answer streams a word at a time the way a model's would.
 *
 * Nothing here calls a model. The lookup reads orders.json from the agent's
 * folder when it starts, so every answer is exact, and an order that is not
 * there makes the tool fail the way a real lookup would.
 */

import { readFileSync } from 'node:fs'

interface Order {
  readonly status: string
  readonly carrier?: string
  readonly shippedOn?: string
  readonly arrivesOn?: string
  readonly readyBy?: string
}

const orders = JSON.parse(readFileSync('orders.json', 'utf8')) as Record<string, Order>

const pause = (ms: number): Promise<void> => new Promise((done) => setTimeout(done, ms))

function describe(id: string, order: Order): string {
  if (order.status === 'shipped') {
    return `Order ${id} shipped with ${order.carrier ?? 'the carrier'} on ${order.shippedOn ?? 'its ship date'} and should arrive on ${order.arrivesOn ?? 'soon'}.`
  }
  return `Order ${id} is still being packed and will be ready to ship by ${order.readyBy ?? 'soon'}.`
}

export async function* handler(prompt: string): AsyncGenerator<unknown> {
  if (prompt.trim().toLowerCase() === 'raise') throw new Error('the agent was asked to raise')

  const id = /\b(\d{4})\b/.exec(prompt)?.[1]
  let answer: string
  if (id === undefined) {
    answer = 'Which order do you mean? Give me the four digit number from your confirmation email.'
  } else {
    yield { type: 'tool_call_start', id: 'lookup_1', name: 'lookup_order' }
    yield { type: 'tool_call_args', id: 'lookup_1', delta: JSON.stringify({ orderId: id }) }
    yield { type: 'tool_call_end', id: 'lookup_1' }
    await pause(150)
    const order = orders[id]
    if (order === undefined) {
      yield { type: 'tool_result', id: 'lookup_1', output: `No order ${id} exists.`, isError: true }
      answer = `I could not find order ${id}. Check the number on your confirmation email.`
    } else {
      yield { type: 'tool_result', id: 'lookup_1', output: JSON.stringify(order) }
      answer = describe(id, order)
    }
  }

  console.log(`answering: ${answer}`)
  for (const [index, word] of answer.split(' ').entries()) {
    await pause(40)
    yield index === 0 ? word : ` ${word}`
  }
}
