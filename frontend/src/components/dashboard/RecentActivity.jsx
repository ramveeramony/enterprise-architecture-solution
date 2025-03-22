import React from 'react';
import { Link } from 'react-router-dom';
import { Avatar, Timeline } from 'flowbite-react';
import { FiPlus, FiEdit, FiTrash2 } from 'react-icons/fi';
import { format, formatDistanceToNow } from 'date-fns';

const RecentActivity = ({ activities = [] }) => {
  if (!activities || activities.length === 0) {
    return (
      <div className="flex justify-center items-center h-40">
        <p className="text-gray-500 dark:text-gray-400">No recent activity</p>
      </div>
    );
  }

  const getActivityIcon = (type) => {
    if (type.includes('created')) {
      return <FiPlus className="h-4 w-4" />;
    } else if (type.includes('updated')) {
      return <FiEdit className="h-4 w-4" />;
    } else if (type.includes('deleted')) {
      return <FiTrash2 className="h-4 w-4" />;
    }
    return null;
  };

  const getActivityColor = (type) => {
    if (type.includes('created')) {
      return 'success';
    } else if (type.includes('updated')) {
      return 'warning';
    } else if (type.includes('deleted')) {
      return 'failure';
    }
    return 'gray';
  };

  const getActivityLink = (activity) => {
    if (activity.type.includes('element')) {
      const elementId = activity.id.replace('element_', '');
      return `/elements/${elementId}`;
    } else if (activity.type.includes('model')) {
      const modelId = activity.id.replace('model_', '');
      return `/models/${modelId}`;
    }
    return '#';
  };

  const getReadableActivity = (activity) => {
    const action = activity.type.split('_')[1] || '';
    const itemType = activity.type.split('_')[0] || '';
    return `${action} ${itemType}`;
  };

  const getTimeAgo = (timestamp) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch (e) {
      return 'recently';
    }
  };

  return (
    <Timeline>
      {activities.map((activity) => (
        <Timeline.Item key={activity.id}>
          <Timeline.Point icon={getActivityIcon(activity.type)} color={getActivityColor(activity.type)} />
          <Timeline.Content>
            <Timeline.Time>{getTimeAgo(activity.timestamp)}</Timeline.Time>
            <Timeline.Title>
              <Link to={getActivityLink(activity)} className="hover:underline">
                {activity.name}
              </Link>
            </Timeline.Title>
            <Timeline.Body>
              <div className="flex items-center">
                <Avatar
                  img="https://i.pravatar.cc/150?img=50"
                  size="xs"
                  rounded
                  className="mr-2"
                />
                <span>
                  <span className="font-medium">{activity.user}</span> {getReadableActivity(activity)}
                </span>
              </div>
            </Timeline.Body>
          </Timeline.Content>
        </Timeline.Item>
      ))}
    </Timeline>
  );
};

export default RecentActivity;