# appmesh_k8s_retry_test

## Overall

ここにあるコードは、aws-app-mesh-examplesリポジトリのhowto-k8s-retry-policyのコードを元に、ローリングデプロイ時に旧コンテナでまだ処理中であったリクエストが旧コンテナが終了した時に、一度失敗した後に適切に新コンテナにリトライされるかをテストするために、コードを一部改良したものである。

https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/howto-k8s-retry-policy

## Prerequisite

- Set up Amazon EKS
- Set up App Mesh Kubernetes controller
  - https://docs.aws.amazon.com/eks/latest/userguide/mesh-k8s-integration.html

## Set up

各オブジェクトを起動。

```bash
$ git clone git@github.com:yuto425/appmesh_k8s_retry_test.git
$ cd appmesh_k8s_retry_test
$ kubectl apply -f manifest.yml 
namespace/howto-k8s-retry-policy created
mesh.appmesh.k8s.aws/howto-k8s-retry-policy created
virtualnode.appmesh.k8s.aws/front created
virtualnode.appmesh.k8s.aws/blue created
virtualservice.appmesh.k8s.aws/color created
virtualrouter.appmesh.k8s.aws/color created
service/front created
deployment.apps/front created
service/color created
deployment.apps/blue created
```

動いていることを確認。

```bash
$ kubectl get pod -n howto-k8s-retry-policy
NAME                     READY   STATUS    RESTARTS   AGE
blue-758d75c957-hz6nw    3/3     Running   0          3m8s
front-6b8b85974f-xgczg   3/3     Running   0          3m8s
```

## Retry Test

front Podからcolor(blue) Pod に対してリクエストを送り、リトライが正しく行われることを確認する。

### 正常系

エンドポイント `/ok` にリクエストを送る。正常にリクエストが返ってくることを期待する。

```bash
$ kubectl exec -it front-6b8b85974f-xgczg \
               -c app \
               -n howto-k8s-retry-policy \
               -- curl color.howto-k8s-retry-policy.svc.cluster.local:5000/ok
ok
```

リクエストが届いていることを確認。

```bash
$ kubectl logs -f blue-758d75c957-hz6nw -c app -n howto-k8s-retry-policy
[2020-09-04 04:46:53 +0000] [8] [DEBUG] GET /ok
```

### 異常系

エンドポイント `/ng` にリクエストを送る。4回リトライされて(計5回)、500番が返ってくることを期待する。

```bash
$ kubectl exec -it front-6b8b85974f-xgczg \
               -c app \
               -n howto-k8s-retry-policy \
               -- curl color.howto-k8s-retry-policy.svc.cluster.local:5000/ng
ng
```

リトライされていることを確認。

```bash
$ kubectl logs -f blue-758d75c957-hz6nw -c app -n howto-k8s-retry-policy
[2020-09-04 04:47:07 +0000] [10] [DEBUG] GET /ng
[2020-09-04 04:47:07 +0000] [13] [DEBUG] GET /ng
[2020-09-04 04:47:07 +0000] [10] [DEBUG] GET /ng
[2020-09-04 04:47:07 +0000] [13] [DEBUG] GET /ng
[2020-09-04 04:47:07 +0000] [16] [DEBUG] GET /ng
```

### デプロイ時のリトライ

エンドポイント `/heavy` に対してリクエストを送る。このエンドポイントは時間のかかる処理を想定して60秒スリープしてからokを返す。
今回は詳細をしりたいので、リクエスト時のcurlに-vオプションをつける。

```bash
$ kubectl exec -it front-6b8b85974f-xgczg \
               -c app \
               -n howto-k8s-retry-policy \
               -- curl -v color.howto-k8s-retry-policy.svc.cluster.local:5000/heavy
```

blue Podが上記のリクエストを処理中に、別ターミナルを開いてblue Podを新しく作り替える(デプロイ)。
kubectl applyコマンドでは設定に変更がない場合はPodが作り変わらないので、patchを用いて強制的にアップデートを行う。

```bash
$ kubectl patch deployment blue -n howto-k8s-retry-policy -p "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"date\":\"`date +'%s'`\"}}}}}"
```

リクエストを送ったターミナルに戻り、Podの作り替えが完了するのを待つ。
旧Podが終了した時にリクエストが一度失敗してから新Podにリトライされ、さらに60秒待つとokが返ってくることを想定したが、実際は旧Podが削除された段階でエラーが返ってきた。

```bash
* Connected to color.howto-k8s-retry-policy.svc.cluster.local (10.100.73.109) port 5000 (#0)
> GET /heavy HTTP/1.1
> Host: color.howto-k8s-retry-policy.svc.cluster.local:5000
> User-Agent: curl/7.64.0
> Accept: */*
> 
< HTTP/1.1 503 Service Unavailable
< content-length: 95
< content-type: text/plain
< date: Fri, 04 Sep 2020 05:11:34 GMT
< server: envoy
< 
* Connection #0 to host color.howto-k8s-retry-policy.svc.cluster.local left intact
upstream connect error or disconnect/reset before headers. reset reason: connection termination
```

新Podにリクエストがきた形跡は特になし。

```bash
$ kubectl logs -f blue-856ff9d8d-zpwf7 -c app -n howto-k8s-retry-policy
```