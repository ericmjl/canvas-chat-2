<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Background,
		Controls,
		MiniMap,
		SvelteFlow,
		SvelteFlowProvider,
		type Connection,
		type Edge,
		type Node,
		type Viewport
	} from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import * as api from '$lib/api';
	import type { MessageEdge, MessageNode, MessageRole, ProviderConfig } from '$lib/types';

	type ChatNodeData = {
		label: string;
		role: MessageRole;
		content: string;
	};

	type ChatNode = Node<ChatNodeData, string | undefined>;

	const CONVERSATION_ID = 'default';

	let nodes = $state.raw<ChatNode[]>([]);
	let edges = $state.raw<Edge[]>([]);
	let viewport = $state<Viewport>({ x: 0, y: 0, zoom: 1 });

	let flowW = $state(0);
	let flowH = $state(0);

	let providers = $state.raw<ProviderConfig[]>([]);
	/** Empty string = let the server use the active provider. */
	let selectedProviderId = $state('');

	let providerFormId = $state('');
	let providerFormModel = $state('');
	let providerFormApiBase = $state('');
	let providerFormApiKeyEnvVar = $state('');
	let providerFormIsActive = $state(false);

	let selectedNodeId = $state<string | null>(null);
	let selectedEdgeId = $state<string | null>(null);
	let panelRole = $state<MessageRole>('human');
	let panelContent = $state('');

	let status = $state<string | null>(null);
	let error = $state<string | null>(null);
	let busy = $state(false);
	let composerMessage = $state('');

	function setError(e: unknown): void {
		error = e instanceof Error ? e.message : String(e);
	}

	function nodeLabel(role: MessageRole, content: string): string {
		const preview =
			content.trim() === '' ? '(empty)' : content.replace(/\s+/g, ' ').slice(0, 72);
		return `${role}: ${preview}`;
	}

	function toFlowNode(n: MessageNode): ChatNode {
		return {
			id: n.id,
			type: 'default',
			position: { x: n.x, y: n.y },
			data: {
				label: nodeLabel(n.role, n.content),
				role: n.role,
				content: n.content
			}
		};
	}

	function toFlowEdge(e: MessageEdge): Edge {
		return {
			id: e.id,
			source: e.source_node_id,
			target: e.target_node_id,
			label: e.label ?? undefined
		};
	}

	async function loadGraph(): Promise<void> {
		const graph = await api.getGraph(CONVERSATION_ID);
		nodes = graph.nodes.map(toFlowNode);
		edges = graph.edges.map(toFlowEdge);
	}

	function flowCenter(): { x: number; y: number } {
		const vp = viewport;
		if (flowW < 1 || flowH < 1) {
			return { x: 0, y: 0 };
		}
		return {
			x: (flowW / 2 - vp.x) / vp.zoom,
			y: (flowH / 2 - vp.y) / vp.zoom
		};
	}

	async function addNode(role: MessageRole): Promise<void> {
		const { x, y } = flowCenter();
		busy = true;
		error = null;
		try {
			await api.createNode(CONVERSATION_ID, { role, content: '', x, y });
			await loadGraph();
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	async function submitComposerMessage(): Promise<void> {
		// @spec CCHAT-COMPOSER-001, CCHAT-COMPOSER-005
		const message = composerMessage.trim();
		if (message === '') return;
		const { x, y } = flowCenter();
		busy = true;
		error = null;
		try {
			await api.createNode(CONVERSATION_ID, { role: 'human', content: message, x, y });
			composerMessage = '';
			await loadGraph();
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	function handleComposerKeydown(e: KeyboardEvent): void {
		// @spec CCHAT-COMPOSER-002, CCHAT-COMPOSER-003
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			void submitComposerMessage();
		}
	}

	async function saveSelectedNode(): Promise<void> {
		if (!selectedNodeId) return;
		busy = true;
		error = null;
		try {
			await api.updateNode(selectedNodeId, { role: panelRole, content: panelContent });
			await loadGraph();
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	async function deleteSelectedEdge(): Promise<void> {
		if (!selectedEdgeId) return;
		busy = true;
		error = null;
		try {
			await api.deleteEdge(selectedEdgeId);
			selectedEdgeId = null;
			await loadGraph();
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	async function runGenerateReply(): Promise<void> {
		if (!selectedNodeId) return;
		busy = true;
		error = null;
		try {
			const body =
				selectedProviderId === '' ? {} : { provider_id: selectedProviderId };
			await api.generateReply(selectedNodeId, body);
			await loadGraph();
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	async function saveProviderConfig(): Promise<void> {
		const id = providerFormId.trim();
		const model = providerFormModel.trim();
		if (id === '' || model === '') {
			setError(new Error('Provider id and model are required.'));
			return;
		}
		const base = providerFormApiBase.trim();
		const envVar = providerFormApiKeyEnvVar.trim();
		busy = true;
		error = null;
		try {
			await api.upsertProvider(id, {
				litellm_model: model,
				api_base: base === '' ? null : base,
				api_key_env_var: envVar === '' ? null : envVar,
				is_active: providerFormIsActive
			});
			providers = await api.listProviders();
			if (providerFormIsActive) {
				selectedProviderId = id;
			}
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	async function handleConnect(c: Connection): Promise<void> {
		if (!c.source || !c.target) return;
		busy = true;
		error = null;
		try {
			await api.createEdge(CONVERSATION_ID, {
				source_node_id: c.source,
				target_node_id: c.target
			});
			await loadGraph();
		} catch (e) {
			setError(e);
		} finally {
			busy = false;
		}
	}

	async function handleNodeDragStop(event: {
		targetNode: ChatNode | null;
	}): Promise<void> {
		const n = event.targetNode;
		if (!n) return;
		try {
			await api.updateNode(n.id, { x: n.position.x, y: n.position.y });
		} catch (e) {
			setError(e);
			await loadGraph();
		}
	}

	function handleNodeClick(event: { node: ChatNode }): void {
		selectedNodeId = event.node.id;
		selectedEdgeId = null;
		panelRole = event.node.data.role;
		panelContent = event.node.data.content;
	}

	function handleEdgeClick(event: { edge: Edge }): void {
		selectedEdgeId = event.edge.id;
		selectedNodeId = null;
	}

	function handlePaneClick(): void {
		selectedNodeId = null;
		selectedEdgeId = null;
	}

	onMount(() => {
		(async () => {
			status = 'Loading…';
			error = null;
			try {
				const [plist] = await Promise.all([api.listProviders(), loadGraph()]);
				providers = plist;
			} catch (e) {
				setError(e);
			} finally {
				status = null;
			}
		})();
	});
</script>

<div class="shell">
	<div class="canvas-wrap" bind:clientWidth={flowW} bind:clientHeight={flowH}>
		<SvelteFlowProvider>
			<SvelteFlow
				bind:nodes
				bind:edges
				fitView
				minZoom={0.2}
				maxZoom={1.5}
				bind:viewport
				nodesConnectable={true}
				onnodedragstop={handleNodeDragStop}
				onconnect={handleConnect}
				onnodeclick={handleNodeClick}
				onedgeclick={handleEdgeClick}
				onpaneclick={handlePaneClick}
			>
				<Background gap={16} />
				<Controls />
				<MiniMap zoomable pannable />
			</SvelteFlow>
		</SvelteFlowProvider>
	</div>

	<aside class="panel">
		<header class="panel-head">
			<h1>Canvas chat</h1>
			<p class="muted">API: {api.API_BASE}</p>
		</header>

		{#if status}
			<p class="status">{status}</p>
		{/if}
		{#if error}
			<p class="err" role="alert">{error}</p>
		{/if}

		<section class="section composer-section">
			<h2>New message</h2>
			<p class="muted composer-hint">Enter sends · Shift+Enter newline</p>
			<label class="field">
				<span>Message</span>
				<textarea
					bind:value={composerMessage}
					rows={4}
					disabled={busy}
					onkeydown={handleComposerKeydown}
				></textarea>
			</label>
			<div class="row">
				<button type="button" disabled={busy} onclick={() => void submitComposerMessage()}>
					Send
				</button>
			</div>
		</section>

		<section class="section">
			<h2>Add nodes</h2>
			<div class="row">
				<button type="button" disabled={busy} onclick={() => addNode('human')}>
					+ Human
				</button>
				<button type="button" disabled={busy} onclick={() => addNode('system')}>
					+ System
				</button>
			</div>
		</section>

		<section class="section">
			<h2>Provider</h2>
			<label class="field">
				<span>Model / provider</span>
				<select bind:value={selectedProviderId} disabled={busy}>
					<option value="">Default (active on server)</option>
					{#each providers as p (p.id)}
						<option value={p.id}>
							{p.id} — {p.litellm_model}{p.is_active ? ' (active)' : ''}
						</option>
					{/each}
				</select>
			</label>

			<h3 class="subhead">Configure provider</h3>
			<label class="field">
				<span>Provider id</span>
				<input type="text" bind:value={providerFormId} disabled={busy} autocomplete="off" />
			</label>
			<label class="field">
				<span>LiteLLM model</span>
				<input type="text" bind:value={providerFormModel} disabled={busy} autocomplete="off" />
			</label>
			<label class="field">
				<span>API base (optional)</span>
				<input type="text" bind:value={providerFormApiBase} disabled={busy} autocomplete="off" />
			</label>
			<label class="field">
				<span>API key env var (optional)</span>
				<input
					type="text"
					bind:value={providerFormApiKeyEnvVar}
					disabled={busy}
					autocomplete="off"
				/>
			</label>
			<label class="field checkbox-field">
				<span>Options</span>
				<span class="row checkbox-row">
					<input type="checkbox" bind:checked={providerFormIsActive} disabled={busy} />
					Active on server
				</span>
			</label>
			<div class="row">
				<button type="button" disabled={busy} onclick={saveProviderConfig}>Save provider</button>
			</div>
		</section>

		<section class="section">
			<h2>Selected node</h2>
			{#if selectedNodeId}
				<p class="muted mono">{selectedNodeId}</p>
				<label class="field">
					<span>Role</span>
					<select bind:value={panelRole} disabled={busy}>
						<option value="human">human</option>
						<option value="ai">ai</option>
						<option value="system">system</option>
					</select>
				</label>
				<label class="field">
					<span>Content</span>
					<textarea bind:value={panelContent} rows={8} disabled={busy}></textarea>
				</label>
				<div class="row">
					<button type="button" disabled={busy} onclick={saveSelectedNode}>Save</button>
					<button type="button" disabled={busy} onclick={runGenerateReply}>
						Generate AI reply
					</button>
				</div>
			{:else}
				<p class="muted">Click a node to edit.</p>
			{/if}
		</section>

		<section class="section">
			<h2>Selected edge</h2>
			{#if selectedEdgeId}
				<p class="muted mono">{selectedEdgeId}</p>
				<button type="button" disabled={busy} onclick={deleteSelectedEdge}>
					Delete edge
				</button>
			{:else}
				<p class="muted">Click an edge, then delete.</p>
			{/if}
		</section>
	</aside>
</div>

<style>
	:global(html, body) {
		height: 100%;
		margin: 0;
	}

	.shell {
		display: flex;
		height: 100vh;
		min-height: 0;
		background: #0f1419;
		color: #e6edf3;
		font-family:
			system-ui,
			-apple-system,
			Segoe UI,
			sans-serif;
	}

	.canvas-wrap {
		flex: 1;
		min-width: 0;
		min-height: 0;
		position: relative;
	}

	.canvas-wrap :global(.svelte-flow) {
		width: 100%;
		height: 100%;
	}

	.panel {
		width: 320px;
		flex-shrink: 0;
		border-left: 1px solid #30363d;
		padding: 1rem;
		overflow: auto;
		background: #161b22;
	}

	.panel-head h1 {
		margin: 0 0 0.25rem;
		font-size: 1.15rem;
		font-weight: 600;
	}

	.muted {
		color: #8b949e;
		font-size: 0.85rem;
		margin: 0;
	}

	.mono {
		font-family: ui-monospace, monospace;
		word-break: break-all;
	}

	.status {
		color: #58a6ff;
	}

	.err {
		color: #f85149;
		font-size: 0.9rem;
	}

	.section {
		margin-top: 1.25rem;
		padding-top: 1rem;
		border-top: 1px solid #21262d;
	}

	.section h2 {
		margin: 0 0 0.75rem;
		font-size: 0.95rem;
		font-weight: 600;
		color: #c9d1d9;
	}

	.subhead {
		margin: 1rem 0 0.5rem;
		font-size: 0.85rem;
		font-weight: 600;
		color: #c9d1d9;
	}

	.checkbox-field .checkbox-row {
		align-items: center;
	}

	.checkbox-row input[type='checkbox'] {
		width: auto;
		margin: 0;
		accent-color: #58a6ff;
	}

	.row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	button {
		cursor: pointer;
		border: 1px solid #30363d;
		background: #21262d;
		color: #e6edf3;
		border-radius: 6px;
		padding: 0.45rem 0.75rem;
		font-size: 0.875rem;
	}

	button:hover:not(:disabled) {
		background: #30363d;
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		margin-bottom: 0.75rem;
	}

	.field span {
		font-size: 0.8rem;
		color: #8b949e;
	}

	select,
	textarea,
	input[type='text'] {
		font: inherit;
		color: #e6edf3;
		background: #0d1117;
		border: 1px solid #30363d;
		border-radius: 6px;
		padding: 0.45rem 0.5rem;
	}

	textarea {
		resize: vertical;
		min-height: 6rem;
	}

	.composer-section .composer-hint {
		margin: -0.35rem 0 0.5rem;
	}
</style>
