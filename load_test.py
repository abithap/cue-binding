#!~/test-binding/env/bin/python

import keystoneclient
import datetime
import time
import logging

from cueclient.v1 import client
logging.basicConfig(filename='cue-binding.log', level=logging.INFO)
logger = logging.getLogger(__name__)

# cluster details
cluster_size = 3
cluster_nic = "b9f03736-4933-4ab4-9b1e-a393513b5312"
cluster_name = "test_cluster"
cluster_flavor = "101"


class Cluster(object):
    def __init__(self, cue_cli):
        self.create_start_time = 0
        self.delete_start_time = 0
        self.cueObject = cue_cli


# Cluster create
    def create_cluster(self):
        create_response = self.cueObject.clusters.create(
            name=cluster_name, nic=cluster_nic,
            flavor=cluster_flavor, size=cluster_size, volume_size="0")
        self.create_start_time = datetime.datetime.now()
        return create_response

# Cluster show
    def show_cluster(self, cluster_id):
        return self.cueObject.clusters.get(cluster_id)

# Cluster delete
    def delete_cluster(self, cluster_id):
        self.cueObject.clusters.delete(cluster_id)
        self.delete_start_time = datetime.datetime.now()
        try:
            while self.show_cluster(cluster_id).status == "DELETING":
                go_to_sleep()
        except Exception, e:
            logger.info("Cluster id: '%s' deleted in %s", cluster_id,
                        (datetime.datetime.now()- self.delete_start_time))

# Get cluster status
    def get_status(self, cluster_id):
        return self.cueObject.clusters.get(cluster_id).status

# Get cluster endpoints
    def get_endpoints(self, cluster_id):
        return self.cueObject.clusters.get(cluster_id).end_points


# sleep for 20 seconds
def go_to_sleep():
    time.sleep(20)


# auth url- "http://192.168.233.133:5000/v2.0/" --nic "b2df59c8-7c54-48c7-914a-6ea0459f931a",flavor="8795"

def main():
    # get client object
    auth = keystoneclient.auth.identity.v2.Password(
        auth_url= "http://15.126.209.27:5000/v2.0/",
        username="admin",
        password="password",
        tenant_name="admin"
    )
    session = keystoneclient.session.Session(auth=auth)
    cue_client = client.Client(session=session)

    cluster = Cluster(cue_client)

    # check cluster create
    response = cluster.create_cluster()

    if cluster.get_status(response.id) == "BUILDING":

        for x in range(0, 15):
            if cluster.get_status(response.id) == "BUILDING":
                go_to_sleep()
            else:
                break
        if cluster.get_status(response.id) == "BUILDING":
            logger.error("Cluster:'%s' still in Building state!" % response.id)

        elif cluster.get_status(response.id) == "ERROR":
            logger.error("Cluster id: '%s' cannot be created!" % response.id)

        elif cluster.get_status(response.id) == "ACTIVE":
            if (len((cluster.show_cluster(response.id)).end_points)) != cluster_size:
                logger.error("Cluster endpoints not created properly")
            else:
                logger.info("Cluster id: '%s' created in %s", response.id,
                            (datetime.datetime.now() - cluster.create_start_time))

    elif cluster.get_status(response.id) == "ERROR":
        logger.error("Cluster creation of id: '%s' error!" % response.id)

    elif cluster.get_status(response.id) == "ACTIVE":
        if len(response.end_points) != 1:
            logger.error("Cluster endpoints not created properly")
        else:
            logger.info("Cluster id: '%s' created in %s", response.id,
                        (datetime.datetime.now() - cluster.create_start_time))

    # delete the cluster
    cluster.delete_cluster(response.id)


if __name__ == '__main__':
    main()