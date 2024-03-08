import { Button } from 'antd';
import { useContext, useMemo } from 'react';
import { NodeProps } from 'reactflow';
import 'reactflow/dist/style.css';
import { NodeDefaultCard } from '../../frontend/components/NodeDefaultCard';
import { HTTP_URL } from '../../frontend/const';
import { GraphContext } from '../../frontend/hooks/graphs';
import { NotificationContext } from '../../frontend/hooks/notification';
import { fetchWithCredentials } from '../../frontend/requests';

export function DebugCustomHttpRequest(node: NodeProps) {
  const { graph } = useContext(GraphContext);
  const { notificationAPI } = useContext(NotificationContext);

  const items = useMemo(
    () => [
      {
        name: 'Panel',
        children: (
          <Button
            onClick={() => {
              fetchWithCredentials(
                HTTP_URL + '/ping',
                notificationAPI,
                (response) => {
                  response.json().then((data) => {
                    notificationAPI.success({
                      message: 'Success',
                      description: `Fetched ${HTTP_URL}/ping: ${JSON.stringify(
                        data,
                      )}`,
                    });
                  });
                },
                () => {},
              );
            }}
          >
            Ping
          </Button>
        ),
      },
    ],
    [notificationAPI],
  );

  if (!graph.nodes[node.id]) {
    // BUG: this might trigger error: Cannot read properties of undefined (reading 'data') during hot reload and delete. This is due to node.id isn't updated and it tries to keep the original component (node still rendered when it shouldn't).
    console.warn(
      'Node ' + node.id + ' of type ' + node.type + ' is not in graph.nodes',
    );
    return <></>;
  }

  return (
    <NodeDefaultCard
      items={items}
      nodeId={node.id}
      nodeType={node.type}
      nodeDataState={node.data.state}
      nodeDataInput={node.data.input}
      nodeDataCachePolicy={node.data.cachePolicy}
      nodeDataOutput={node.data.output}
    />
  );
}
