import { When, Then, Given } from "@cucumber/cucumber"
import { Effect } from "effect"
import { Permission } from "../../../opencode/packages/opencode/src/permission"
import { Agent } from "../../../opencode/packages/opencode/src/agent/agent"
import { AgentWorld } from "../support/hooks"
import assert from "node:assert/strict"

When("I list the available agents", async function (this: AgentWorld) {
  this.agentList = await this.runtime.runPromise(
    Agent.Service.use((svc) => svc.list()),
  )
})

Then('"test" is included in the list as a primary agent', function (this: AgentWorld) {
  const entry = this.agentList.find((a) => a.name === "test")
  assert.ok(entry, `"test" not found among agents: ${this.agentList.map((a) => a.name).join(", ")}`)
  assert.equal(entry.mode, "primary")
})

Given('I have the "test" agent', async function (this: AgentWorld) {
  this.currentAgent = await this.runtime.runPromise(
    Agent.Service.use((svc) => svc.get("test")),
  )
  assert.ok(this.currentAgent, '"test" agent not found')
})

Then('its edit permission is "ask"', function (this: AgentWorld) {
  const action = Permission.evaluate("edit", "*", this.currentAgent!.permission).action
  assert.equal(action, "ask")
})

Then('its bash permission is "ask"', function (this: AgentWorld) {
  const action = Permission.evaluate("bash", "*", this.currentAgent!.permission).action
  assert.equal(action, "ask")
})

Then("it has a non-empty system prompt", function (this: AgentWorld) {
  assert.ok(
    this.currentAgent!.prompt?.trim().length,
    "system prompt is empty or missing",
  )
})
