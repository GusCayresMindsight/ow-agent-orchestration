import { BeforeAll, AfterAll, Before, setWorldConstructor } from "@cucumber/cucumber"
import { Effect, Layer, ManagedRuntime } from "effect"
import * as fs from "node:fs/promises"
import * as os from "node:os"
import * as path from "node:path"
import { Agent } from "../../../opencode/packages/opencode/src/agent/agent"
import { Plugin } from "../../../opencode/packages/opencode/src/plugin"
import { Provider } from "../../../opencode/packages/opencode/src/provider/provider"
import { Auth } from "../../../opencode/packages/opencode/src/auth"
import { Config } from "../../../opencode/packages/opencode/src/config/config"
import { Skill } from "../../../opencode/packages/opencode/src/skill"
import { RuntimeFlags } from "../../../opencode/packages/opencode/src/effect/runtime-flags"
import { InstanceRef } from "../../../opencode/packages/opencode/src/effect/instance-ref"
import { ProjectID } from "../../../opencode/packages/opencode/src/project/schema"
import type { InstanceContext } from "../../../opencode/packages/opencode/src/project/instance-context"

// A runtime wrapper that automatically provides InstanceRef for every runPromise call.
export type BoundRuntime = {
  runPromise: <A>(effect: Effect.Effect<A, never, Agent.Service>) => Promise<A>
}

export class AgentWorld {
  agentList: Agent.Info[] = []
  currentAgent: Agent.Info | undefined
  runtime!: BoundRuntime
  tmpDir: string = ""
}

setWorldConstructor(AgentWorld)

// Shared across all scenarios — created once in BeforeAll, torn down in AfterAll.
let _tmpDir = ""
let _instanceCtx: InstanceContext
let _runtime: ManagedRuntime.ManagedRuntime<Agent.Service, never>

const agentLayer = Agent.layer.pipe(
  Layer.provide(Plugin.defaultLayer),
  Layer.provide(Provider.defaultLayer),
  Layer.provide(Auth.defaultLayer),
  Layer.provide(Config.defaultLayer),
  Layer.provide(Skill.defaultLayer),
  Layer.provide(RuntimeFlags.defaultLayer),
)

BeforeAll(async () => {
  _tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ow-bdd-"))

  // Minimal InstanceContext — agent.ts only uses directory and worktree for
  // path-based permission whitelisting; project.id is not read by the Agent layer.
  _instanceCtx = {
    directory: _tmpDir,
    worktree: _tmpDir,
    project: {
      id: ProjectID.make("bdd-test"),
      worktree: _tmpDir,
      time: { created: Date.now(), updated: Date.now() },
      sandboxes: [],
    },
  }

  _runtime = ManagedRuntime.make(agentLayer)
})

AfterAll(async () => {
  await _runtime.dispose()
  await fs.rm(_tmpDir, { recursive: true, force: true })
})

// Each scenario gets a fresh world; bind the shared runtime + tmpDir onto it.
Before(function (this: AgentWorld) {
  this.tmpDir = _tmpDir
  this.runtime = {
    runPromise: <A>(effect: Effect.Effect<A, never, Agent.Service>) =>
      _runtime.runPromise(effect.pipe(Effect.provideService(InstanceRef, _instanceCtx))),
  }
})
