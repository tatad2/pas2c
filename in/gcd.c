int x, y;
int gcd(int a,int b) {
	int gcd;
	if(b==0) {
		gcd=a;
	}
	else {
		gcd=gcd(b,a%b);
	}
	return gcd;
}
int main() {
	scanf("%d%d", x, y);
	printf("%d\n", gcd(x,y));
	return 0;
}
